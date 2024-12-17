
from functools import partial
from ..utils.gui_box import AnchoredGuiBox


class WidgetSet():
    def __init__(self, gui_object, **kwargs):
        self.gui = gui_object
        self.kwargs = kwargs
        self.params = []

        self.pre_trigger_hooks = []
        self.post_trigger_hooks = []
        self.status = dict()

    def append_param(self, widget_id, get_param1):
        self.params.append((widget_id, get_param1))

    def get_params(self):
        r = dict((widget_id, get_param1())
                 for widget_id, get_param1 in self.params)
        return r

    def install_widgets(self, widget_list):
        for w in widget_list:
            w.install(self,
                      pre_trigger_hooks=self.pre_trigger_hooks,
                      post_trigger_hooks=self.post_trigger_hooks)

    # ws = WidgetSet(box, ax=ax)

    # def _append_widget(self, widgetwidget_set, widget):
    #     widget_set.append_param(self.widget_id,
    #                             partial(self.get_param1, widget))


class Widget():
    def __init__(self, widget_id, value=None, label=None,
                 on_trigger=None):
        self.widget_id = widget_id
        self.value = value
        self.label = label
        self.on_trigger = on_trigger

        "on_trigger(self, widget_params, user_params)"

    def get_param1(self, widget):
        "return param value"

        raise RuntimeError("Need to be implmented by the derived class")

    def create_widget(self, widget_set, on_trigger):
        "should return the created widget object"

        raise RuntimeError("Need to be implmented by the derived class")

    def install(self, widget_set,
                pre_trigger_hooks=None, post_trigger_hooks=None):

        if pre_trigger_hooks is None:
            pre_trigger_hooks = []

        if post_trigger_hooks is None:
            post_trigger_hooks = []

        def _on_trigger(*kl, **kw):
            widget_set_kwargs = widget_set.kwargs
            user_params = widget_set.get_params()

            if pre_trigger_hooks:
                for _f in pre_trigger_hooks:
                    _f(self, widget_set_kwargs, user_params)

            if self.on_trigger is not None:
                self.on_trigger(self, widget_set_kwargs, user_params)

            if post_trigger_hooks:
                for _f in post_trigger_hooks:
                    _f(self, widget_set_kwargs, user_params)

        w = self.create_widget(widget_set, _on_trigger)

        widget_set.append_param(self.widget_id,
                                partial(self.get_param1, w))

        return w


class Input(Widget):

    def get_param1(self, widget):
        return widget.text

    def create_widget(self, widget_set, on_trigger):
        gui = widget_set.gui
        label = self.widget_id if self.label is None else self.label
        # on_submit = self.on_submit

        inp = gui.append_labeled_textbox(label, 30, 20,
                                         initial_text=str(self.value))

        inp.on_submit(on_trigger)

        return inp


class Check(Widget):
    def __init__(self, widget_id, check_labels, check_values=None,
                 on_trigger=None):
        self.check_labels = check_labels
        self.check_values = check_values

        Widget.__init__(self, widget_id, on_trigger=on_trigger)

    def get_param1(self, widget):
        return widget.get_status()

    def create_widget(self, widget_set, on_trigger):
        gui = widget_set.gui

        vv = ([False for v in self.chack_labels] if self.check_values is None
              else self.check_values)

        w = gui.append_check_buttons(self.check_labels,
                                     vv)

        w.on_clicked(on_trigger)

        return w


class Radio(Widget):
    def __init__(self, widget_id, radio_labels, radio_values,
                 value=None, label=None,
                 on_trigger=None):
        self.radio_labels = radio_labels
        self.radio_values = radio_values

        Widget.__init__(self, widget_id, value=value, label=label,
                        on_trigger=on_trigger)

    def get_param1(self, widget):
        return widget.get_selected_value()

    def create_widget(self, widget_set, on_trigger):
        gui = widget_set.gui

        v = self.radio_values[0] if self.value is None else self.value

        w = gui.append_radio_buttons(self.radio_labels,
                                     active=self.radio_values.index(v),
                                     values=self.radio_values)

        w.on_clicked(on_trigger)

        return w


class Button(Widget):
    def __init__(self, widget_id, label=None,
                 on_trigger=None):

        Widget.__init__(self, widget_id, label=label,
                        on_trigger=on_trigger)

    def get_param1(self, widget):
        return None

    def create_widget(self, widget_set, on_trigger):
        gui = widget_set.gui

        label = self.widget_id if self.label is None else self.label
        w = gui.append_button(label)
        w.on_clicked(on_trigger)

        return w


if False:
    radio_labels1 = ('level 1', 'level 2')
    # radio_return_values1 = [1, 2]
    # a = radio_return_values1.index(params["remove_level"])
    v, vv = params["remove_level"], [1, 2]
    radio_buttons1 = box.gui.append_radio_buttons(radio_labels1,
                                                  active=vv.index(v),
                                                  values=vv)
    # radio_labels = ('Guard', 'Level 2', 'Level 3')
    # radio_buttons = box.gui.append_radio_buttons(radio_labels, active=1)

# def kk():
#     [Input("vmax", label="vmax", value=vmax,
#            cb=change_clim),  # ["vmax", "input", "vmax", vmax],
#      Input("vmin", label="vmin", value=vmax,
#            cb=change_clim),  # ["vmin", "input", "vmin", vmin],
#      Check("smooth", ["Smooth"], values=[False],
#            cb=hzfunc), # ["smooth", "check", ["Smooth"], [False]],
#      Radio("remove_level", ["Level 1", "Level 2"],
#            values=[1, 2], active=0,
#            cb=hzfunc),  # ["remove_level", "radio", ["Level 1", "Level2"], [1, 2], 0],
#      Radio("bg_sub_mode", ["none", "sky"],
#            cb=hzfunc)
#     ]


def setup_gui(ax):
    im = ax.imshow([[1, 2], [3, 4]], interpolation="none")

    fig = ax.figure

    busy_text = ax.annotate("busy...", (0, 1), va="top", ha="left",
                            xycoords="figure fraction")
    busy_text.set_visible(False)

    box = AnchoredGuiBox(fig, ax, 80, align="center", pad=0, sep=5)
    ax.add_artist(box)

    def on_change(w, kl, user_params):
        # vmax = float(user_params["vmax"])
        # im.set_clim(0, vmax)
        print(w, kl, user_params)

        fig.canvas.draw()

    widgets = [
        Input("vmax", value="30", label="vmax",
              on_trigger=on_change),
        Input("vmin", value="-10", label="vmin",
              on_trigger=on_change),
        Radio("level", ["level 1", "level 2"], [1, 2],
              value=2,
              on_trigger=on_change),
        Check("smooth", ["smooth"], [False],
              on_trigger=on_change),
        Button("Save & Quit")
    ]

    ws = WidgetSet(box.gui, ax=ax)

    def set_busy(*kl, **kwargs):
        busy_text.set_visible(True)
        fig.canvas.draw()

    def unset_busy(*kl, **kwargs):
        busy_text.set_visible(False)
        fig.canvas.draw()

    ws.pre_trigger_hooks.append(set_busy)
    ws.post_trigger_hooks.append(unset_busy)

    ws.install_widgets(widgets)

    # for w in widgets:
    #     w.install(ws)


def setup_basic_gui(ax, params, widgets, save_button_label="Quit"):

    from ..utils.gui_box import AnchoredGuiBox
    from ..utils.gui_box_helper import WidgetSet, Input, Radio, Check, Button

    fig = ax.figure

    busy_text = ax.annotate("busy...", (0, 1), va="top", ha="left",
                            xycoords="figure fraction")
    busy_text.set_visible(False)

    box = AnchoredGuiBox(fig, ax, 80, align="center", pad=0, sep=5)
    ax.add_artist(box)

    ws = WidgetSet(box.gui, ax=ax)

    widgets_pre = []

    def func_save(*kl):
        ws.status["to_save"] = True
        import matplotlib.pyplot as plt
        plt.close(fig)

    widgets_post = [
        Button(save_button_label, on_trigger=func_save)
    ]

    widgets = widgets_pre + widgets + widgets_post

    def set_busy(*kl, **kwargs):
        busy_text.set_visible(True)
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

    def unset_busy(*kl, **kwargs):
        busy_text.set_visible(False)
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

    ws.pre_trigger_hooks.append(set_busy)
    ws.post_trigger_hooks.append(unset_busy)

    ws.install_widgets(widgets)

    return box, ws


def main():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1)
    setup_gui(ax)

    plt.show()


if __name__ == '__main__':
    main()
