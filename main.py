# coding=utf-8
import wx
import time
import threading
import C2B
import tempfile
import cv2
import addSPN
import shutil
import process
import Score
import os.path as path
import datetime


def addlog(msg):
    """
        打印log方法
        :param msg:
        :return:
        """

    def annofunc(func):
        def innerfunc(self, *args, **kwargs):
            self.log(u"开始进行" + msg)
            start = time.time()
            ret = func(self, *args, **kwargs)
            end = time.time()
            self.log(msg + u"完成,共耗时%5.3f秒" % ((end - start),))
            return ret

        return innerfunc

    return annofunc


class PicFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)

        # 初始化操作
        self.ordPath = "lena.jpg"
        self.ordSave = self.ordPath
        self.tempfile = "lena.jpg"

        # 自身设定
        self.SetBackgroundColour(wx.WHITE)
        self.icon = wx.Icon("icon.png")
        self.SetIcon(self.icon)
        # 目录
        self.bar = wx.MenuBar()
        self.file = wx.Menu(title=u"文件")
        self.bar.Append(self.file, title=u"文件")
        open = self.file.Append(wx.ID_ANY, text=u"打开")

        # 创建sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 左半部分
        self.leftsizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.leftsizer, flag=wx.ALL, border=5)
        self.orgImg = DrawPanel(self, wx.ID_ANY, size=(250, 280), style=wx.SIZE_FORCE)
        self.leftsizer.Add(self.orgImg, flag=wx.ALL, border=10)
        self.tarImg = DrawPanel(self, wx.ID_ANY, size=(250, 280), style=wx.SIZE_FORCE)
        self.leftsizer.Add(self.tarImg, flag=wx.ALL, border=10)
        self.socre_console = wx.TextCtrl(self, wx.ID_ANY, size=(250, 20))
        self.socre_console.SetEditable(False)
        self.score_text = wx.StaticText(self, wx.ID_ANY, size=(250, 20), label=u"图片相似度：")
        self.leftsizer.Add(self.score_text, flag=wx.LEFT|wx.RIGHT, border=10)
        self.leftsizer.Add(self.socre_console, flag=wx.LEFT|wx.RIGHT, border=10)

        # 右半部分
        self.rightsizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.rightsizer, flag=wx.ALL, border=5)
        self.bt_open = wx.Button(self, wx.ID_ANY, label=u"打开", size=(150, 20), style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_bw = wx.Button(self, wx.ID_ANY, label=u"处理成黑白图像", size=(150, 20),
                               style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_replace = wx.Button(self, wx.ID_ANY, label=u"使用处理结果作为原始图像", size=(150, 20),
                               style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_reset = wx.Button(self, wx.ID_ANY, label=u"复原源图像", size=(150, 20),
                               style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_replace.Bind(wx.EVT_BUTTON, self.replace)
        self.bt_reset.Bind(wx.EVT_BUTTON, self.reset)
        self.bt_bw.Bind(wx.EVT_BUTTON, self.c2b)
        self.sl_method = wx.ComboBox(self, value=u"请选择您想使用的处理方式", size=(150, 20), style=wx.CB_SORT,
                                     choices=[u"自适应均值滤波", u"中值滤波", u"均值滤波", u"自适应中值滤波"])
        f = self.sl_method.GetFont()
        f.SetPointSize(8)
        self.sl_method.SetFont(f)
        self.sl_method.SetEditable(False)

        self.bt_process = wx.Button(self, wx.ID_ANY, label=u"处理", size=(150, 20),
                                    style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_gprocess = wx.Button(self, wx.ID_ANY, label=u"多线程处理", size=(150, 20),
                                    style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.s_text = wx.StaticText(self, wx.ID_ANY, label=u"盐噪声:", size=(100, 20))
        self.s_value = wx.TextCtrl(self, wx.ID_ANY, value=u"0", size=(50, 20))
        self.s_value.SetEditable(False)
        self.s_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.s_sizer.Add(self.s_text)
        self.s_sizer.Add(self.s_value)

        self.p_text = wx.StaticText(self, wx.ID_ANY, label=u"椒噪声:", size=(100, 20))
        self.p_value = wx.TextCtrl(self, wx.ID_ANY, value=u"0", size=(50, 20))
        self.p_value.SetEditable(False)
        self.p_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.p_sizer.Add(self.p_text)
        self.p_sizer.Add(self.p_value)

        self.s_slider = wx.Slider(self, id=wx.ID_ANY, value=0, minValue=0, maxValue=100, size=(150, 20), name=u"盐噪声")
        self.p_slider = wx.Slider(self, id=wx.ID_ANY, value=0, minValue=0, maxValue=100, size=(150, 20), name=u"椒噪声")

        self.s_slider.Bind(wx.EVT_SLIDER, self.slider(self.s_value))
        self.p_slider.Bind(wx.EVT_SLIDER, self.slider(self.p_value))

        self.bt_addn = wx.Button(self, wx.ID_ANY, label=u"添加椒盐噪声", size=(150, 20),
                                 style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_addn.Bind(wx.EVT_BUTTON, self.addsanoise)
        self.bt_save = wx.Button(self, wx.ID_ANY, label=u"保存目标图像", size=(150, 20),
                                 style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_ssim = wx.Button(self, wx.ID_ANY, label=u"计算SSIM相似度", size=(150, 20),
                                 style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_psnr = wx.Button(self, wx.ID_ANY, label=u"计算PSNR相似度", size=(150, 20),
                                 style=wx.ALIGN_CENTER | wx.BU_ALIGN_MASK)
        self.bt_open.Bind(wx.EVT_BUTTON, self.open)
        self.bt_save.Bind(wx.EVT_BUTTON, self.save)
        self.bt_ssim.Bind(wx.EVT_BUTTON, self.ssim)
        self.bt_psnr.Bind(wx.EVT_BUTTON, self.psnr)

        # 控制台
        self.console_text = wx.StaticText(self, wx.ID_ANY, label=u"控制台：")
        self.console = wx.TextCtrl(self, wx.ID_ANY, "", size=(150, 200), style=wx.TE_MULTILINE)
        self.console.SetEditable(False)

        self.rightsizer.Add(self.bt_open, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_replace, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_reset, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_bw, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.sl_method, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_process, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_gprocess, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.s_sizer, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.s_slider, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.p_sizer, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.p_slider, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_addn, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_save, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_ssim, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.bt_psnr, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.console_text, flag=wx.ALL, border=5)
        self.rightsizer.Add(self.console, flag=wx.ALL, border=5)

        self.bt_process.Bind(wx.EVT_BUTTON, self.process)
        self.bt_gprocess.Bind(wx.EVT_BUTTON, self.mprocess)

        self.SetSizer(self.sizer)
        self.Size
        self.SetMenuBar(self.bar)
        self.SetSize((466, 720))
        self.MaxSize = (466, 720)
        self.MinSize = (466, 720)

    def open(self, event):
        self.file_dialog = wx.FileDialog(self, u"请选择您想处理的图片", size=(200, 100))
        if self.file_dialog.ShowModal() == wx.ID_OK:
            self.ordPath = self.file_dialog.Path
            self.ordSave = self.ordPath
            self.orgImg.images = self.ordPath
            self.orgImg.Update()
            self.orgImg.Refresh()

    def save(self, event):
        self.file_save_dialog = wx.FileDialog(self, u"请选择您想保存的位置", size=(200, 100), style=wx.FD_SAVE,
                                              wildcard="PNG files (*.png)|*.png|JPEG files (*.jpg)|*.jpg")
        if self.tempfile == "lena.jpg":
            self.alert(u"尚未对图片进行处理，无法保存")
            return
        if self.file_save_dialog.ShowModal() == wx.ID_OK:
            tarpath = self.file_save_dialog.Path
            shutil.copy(self.tempfile, tarpath)
            self.log(u"成功保存至%s位置"%tarpath)

    def replace(self, event):
        self.ordPath = self.tempfile
        self.orgImg.images = self.ordPath
        self.orgImg.Update()
        self.orgImg.Refresh()

    def process(self, event):
        pd = dict(zip([u"自适应均值滤波", u"中值滤波", u"均值滤波", u"自适应中值滤波"],(self.awmf, self.middle, self.mean, self.amf)))
        protype = self.sl_method.Value
        thread = threading.Thread(None, pd[protype])
        thread.start()

    def mprocess(self, event):
        pd = dict(zip([u"自适应均值滤波", u"中值滤波", u"均值滤波", u"自适应中值滤波"],(self.mawmf, self.middle, self.mean, self.amf)))
        protype = self.sl_method.Value
        thread = threading.Thread(None, pd[protype])
        thread.start()

    @addlog(u"中值滤波")
    def middle(self):
        im = process.middle(self.ordPath)
        self.savetemp(im)

    @addlog(u"均值滤波")
    def mean(self):
        im = process.mean(self.ordPath)
        self.savetemp(im)

    @addlog(u"自适应中值滤波")
    def amf(self):
        im = process.amf(self.ordPath)
        self.savetemp(im)

    @addlog(u"自适应均值滤波")
    def awmf(self):
        im = process.awmf(self.ordPath)
        self.savetemp(im)

    @addlog(u"多线程自适应均值滤波")
    def mawmf(self):
        im = process.mawmf(self.ordPath, 5)
        self.savetemp(im)

    def slider(self, target):
        def inner_slider(event):
            value = event.GetEventObject().GetValue()
            target.Value = unicode(value)
        return inner_slider

    @addlog(u"黑白处理")
    def c2b(self, event):
        bim = C2B.c2b(self.ordPath)
        self.savetemp(bim)

    def savetemp(self, bim):
        self.tempfile = tempfile.mktemp(".png", "image")
        cv2.imwrite(self.tempfile, bim)
        self.tarImg.images = self.tempfile
        self.tarImg.Update()
        self.tarImg.Refresh()

    @addlog(u"添加椒盐噪声")
    def addsanoise(self, event):
        nim = addSPN.addspnoise(self.ordPath, self.s_slider.GetValue(), self.p_slider.GetValue())
        self.savetemp(nim)

    def log(self, msg):
        self.console.AppendText(msg)
        self.console.AppendText("\r\n")
        self.console.LineDown()

    def alert(self, msg):
        alert = wx.MessageDialog(self, msg, caption=u"注意", style=wx.CANCEL | wx.CENTRE)
        alert.ShowModal()

    def ssim(self, msg):
        ssimn = Score.SSIM(self.ordPath, self.tempfile)
        self.socre_console.Value = str(ssimn)

    def psnr(self, msg):
        ssimn = Score.PSNR(self.ordPath, self.tempfile)
        self.socre_console.Value = str(ssimn)

    def reset(self, msg):
        self.ordPath = self.ordSave
        self.orgImg.images = self.ordPath
        self.orgImg.Update()
        self.orgImg.Refresh()


class PicApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        self.frame = PicFrame(None, title=u"椒盐噪声的多种处理")
        self.frame.Show()
        self.MainLoop()


class DrawPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.images = "lena.jpg"
        self.Bind(wx.EVT_PAINT, self.onDraw)

    def onDraw(self, event):
        self.dc = wx.PaintDC(self)
        self.dc.BeginDrawing()
        try:
            bitmap = wx.Image(self.images)
            # isize = bitmap.GetSize()
            wsize = self.GetSize()
            bitmap.Rescale(wsize[0], wsize[1], wx.IMAGE_QUALITY_HIGH)
            self.dc.DrawBitmap(wx.BitmapFromImage(bitmap), 0, 0)
        except Exception:
            d = wx.MessageDialog(self, u"文件不是一个图片", style=wx.OK)
            d.ShowModal()


def main():
    app = PicApp()


if __name__ == "__main__":
    main()
