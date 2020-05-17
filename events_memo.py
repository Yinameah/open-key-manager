import wx
import wx.lib.newevent

# C'est pas obvious la différence, mais un commande event est sensé propager ...
YinaEvent, EVT_YINA = wx.lib.newevent.NewEvent()
YinaCommandEvent, EVT_COMMAND_YINA = wx.lib.newevent.NewCommandEvent()


class Win(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.MinSize = (300, 200)

        sizer = wx.BoxSizer()
        self.SetSizer(sizer)

        self.button = wx.Button(self, label="Bouton")
        sizer.Add(self.button)

        self.custom_event_button = wx.Button(self, label="CustomEvent")
        sizer.Add(self.custom_event_button)

        self.Show()

        self.button.Bind(wx.EVT_BUTTON, self.btn_click)
        self.button.Bind(wx.EVT_LEFT_DOWN, self.click_somewhere)
        self.button.Bind(wx.EVT_LEFT_UP, self.click_somewhere)

        self.Bind(wx.EVT_LEFT_DOWN, self.click_somewhere)
        self.Bind(wx.EVT_LEFT_UP, self.click_somewhere)

        self.custom_event_button.Bind(wx.EVT_BUTTON, self.custom_event_button_click)

        self.Bind(EVT_YINA, self.yina_handler)
        self.Bind(EVT_COMMAND_YINA, self.yina_handler)

    def click_somewhere(self, event):

        if event.GetEventType() == wx.EVT_LEFT_DOWN.typeId:
            print("down")
        if event.GetEventType() == wx.EVT_LEFT_UP.typeId:
            print("up")

        if event.GetEventObject() is self.button:
            event.Skip()

    def btn_click(self, event):

        print("Bouton has been clicked")

    def custom_event_button_click(self, event):

        print("Send custom event now ...")
        evt = YinaEvent(arbitrary_attr="foo")
        wx.PostEvent(self, evt)
        print("Send custom command event now...")
        evt = YinaCommandEvent(wx.ID_ANY)
        wx.PostEvent(self, evt)

    def yina_handler(self, event):
        print("a yina event is processed")
        print(event.GetEventType())
        try:
            print("arbitrary_attr :", event.arbitrary_attr)
        except AttributeError:
            print("pas d'attributs passé à l'event")


if __name__ == "__main__":

    app = wx.App()
    frm = Win(parent=None, title="bla")
    app.MainLoop()
