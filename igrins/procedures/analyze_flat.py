import numpy as np
import scipy.ndimage as ni

from scipy.interpolate import CubicSpline

from .. import DESCS
from ..utils.refined_argmax import refined_argmax


def get(obsset, ap, offset=5.):

    hdu = obsset.load_resource_for(("flat_on", DESCS["FLAT_DERIV"]))
    im_deriv = hdu[0].data
    yi, xi = np.indices(im_deriv.shape)

    ol = []
    for o in ap.orders_to_extract:
        y0 = ap(o, ap.xi, 0.)
        y1 = ap(o, ap.xi, 1.)

        ydiff0 = yi - y0[np.newaxis, :]
        msk0 = (-offset < ydiff0) & (ydiff0 < offset)

        ydiff1 = yi - y1[np.newaxis, :]
        msk1 = (-offset < ydiff1) & (ydiff1 < offset)

        ol.append(dict(order=o, ybottom=y0, ytop=y1,
                       bottom_mask=msk0, top_mask=msk1))

    return im_deriv, ol


def get_1st_n_2nd_moment(imderiv, msk, yi):
    "msk : mask, ydiff: yindex - aperture"

    imd1 = np.ma.array(np.clip(imderiv, 0, np.inf), mask=~msk).filled(np.nan)
    yy = np.ma.array(yi, mask=~msk, dtype="d").filled(np.nan)

    ws = np.nansum(imd1, axis=0)
    ys = np.nansum(yy * imd1, axis=0)
    y1 = ys / ws

    y2s = np.nansum((yy - y1)**2 * imd1, axis=0)
    y2 = y2s / ws

    return y1, y2


def get_ys_array(imderiv, ol, orange):
    oo = dict((_["order"], _) for _ in ol)
    yss0 = []
    yss1 = []

    yi, xi = np.indices(imderiv.shape)

    for o in orange:
        _ = oo.get(o, None)
        if _ is None:
            yss0.append(np.zeros(imderiv.shape[-1]))
            yss1.append(np.zeros(imderiv.shape[-1]))
            continue

        # msk0, ydiff0, msk1, ydiff1 = _
        ys0 = get_1st_n_2nd_moment(imderiv, _["bottom_mask"], yi)
        ys1 = get_1st_n_2nd_moment(-imderiv, _["top_mask"], yi)

        yss0.append(ys0)
        yss1.append(ys1)

    yss0 = np.array(yss0)
    yss1 = np.array(yss1)

    return {"1st_moment": dict(bottom=yss0[:, 0, :],
                               top=yss1[:, 0, :]),
            "2nd_moment": dict(bottom=yss0[:, 1, :],
                               top=yss1[:, 1, :])}


def get_peak_array(imderiv, ol, orange):
    oo = dict((_["order"], _) for _ in ol)

    yi, xi = np.indices(imderiv.shape)
    yc_list = []

    bottom_deriv = imderiv
    top_deriv = -imderiv

    for o in orange:
        _ = oo.get(o, None)
        if _ is None:
            yc_list.append(np.zeros(imderiv.shape[-1]))
            continue

        ym0, dy0, peak0 = refined_argmax(bottom_deriv, _["bottom_mask"])
        ym1, dy1, peak1 = refined_argmax(top_deriv, _["top_mask"])

        yc_list.append([ym0 + dy0, ym1 + dy1, peak0, -peak1])

    yca = np.array(yc_list)

    return dict(bottom=yca[:, 0, :],
                top=yca[:, 1, :],
                bottom_peak=yca[:, 2, :],
                top_peak=yca[:, 3, :])


def _get_fwhm(imderiv, bottom, bottom_peak, width):

    # zz = np.empty(2*width, dtype="d")
    # zz.fill(np.nan)
    zz = np.zeros(2*width, dtype="d")

    nn = imderiv.shape[0]  # 2048

    sl = [slice(int(y0) - width, int(y0) + width)
          if np.isfinite(y0) else slice(0, 0)
          for y0 in bottom]
    sl = [sl1 if (0 <= sl1.start) or (sl1.stop <= nn - 1) else slice(0, 0)
          for sl1 in sl]
    kk = [r[sl1] if len(r[sl1]) == 2*width else zz
          for sl1, r in zip(sl, imderiv.T)]
    k = np.array(kk)

    # kmax = np.nanmax(k, axis=0)
    x = np.arange(-width, width)
    c = CubicSpline(x, k.T - 0.5*np.nan_to_num(bottom_peak))
    xc = c.roots()

    xc0 = 0.
    # x @ left half
    yleft = [xc11[-1] if len(xc11) else np.nan
             for xc1 in xc for xc11 in [xc1[xc1 < xc0]]]
    yright = [xc11[0] if len(xc11) else np.nan
              for xc1 in xc for xc11 in [xc1[xc1 > xc0]]]

    fwhm_bottom = np.array(yright) - np.array(yleft)

    return fwhm_bottom


def get_fwhm(imderiv, ol, orange, width, ps):
    # oo = dict((_["order"], _) for _ in ol)

    fwhm_bottom_list = []
    fwhm_top_list = []
    # yi, xi = np.indices(imderiv.shape)

    # for i, o in enumerate(orange):
    for i, o in enumerate(orange):
        # _ = oo.get(o, None)

        # if _ is None:
        #     v = np.empty(imderiv.shape[-1], dtype="d")
        #     v.fill(np.nan)
        #     fwhm_list.append((v, v))
        #     continue

        bottom, bottom_peak = ps["bottom"][i], ps["bottom_peak"][i]
        fwhm_bottom = _get_fwhm(imderiv, bottom, bottom_peak, width)
        fwhm_bottom_list.append(fwhm_bottom)

        top, top_peak = ps["top"][i], ps["top_peak"][i]
        fwhm_top = _get_fwhm(-imderiv, top, -top_peak, width)
        fwhm_top_list.append(fwhm_top)

    return dict(bottom=np.array(fwhm_bottom_list),
                top=np.array(fwhm_top_list))


def get_response_mask(obsset):
    jo = obsset.load_resource_for(("register",
                                   DESCS["ORDER_FLAT_JSON"]))
    resp = np.array(jo["fitted_responses"], dtype="d")
    s = np.array(jo["mean_order_specs"], dtype="d")
    msk = (s < resp * 0.9) | (s < 0.1 * np.nanmax(resp, axis=1)[:, np.newaxis])

    msk2 = ni.binary_dilation(msk, structure=[[1, 1, 1]], iterations=5)

    return msk2


if False:
    import igrins
    obsdate = "20171125"
    band = "K"
    config_file = "../../recipe.config"

    recipe_log = igrins.load_recipe_log(obsdate, config_file=config_file)
    obsset = igrins.get_obsset(obsdate, band, recipe_log.iloc[2],
                               config_file=config_file)

    obsset_helper = igrins.get_obsset_helper(obsset)
    ap = obsset_helper.get("aperture")

    imderiv, ol = get(obsset, ap, 7.)

    orange = {"K": range(71, 96),
              "H": range(98, 125)}[band]

    ps = get_peak_array(imderiv, ol, orange)
    ys = get_ys_array(imderiv, ol, orange)

    msk2 = get_response_mask(obsset)


if False:
    # from refined_argmax import refined_argmax

    oi = 10
    clf()
    x = np.arange(2048)
    plot(np.ma.array(ys["1st_moment"]["bottom"][oi] - ap(ap.orders[oi], x, 0),
                     mask=msk2[oi]))

    plot(np.ma.array(ps["bottom"][oi] - ap(ap.orders[oi], x, 0),
                     mask=msk2[oi]))
