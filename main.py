from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPen
from pyqtgraph.examples.syntax import QColor
import cv2
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from myWidget import Ui_Form
import pydicom as pd
import os

class ImageGraphicsLayoutWidget(pg.GraphicsLayoutWidget):

    pageTurnSignal = pyqtSignal(int) #当通过滚轮转页时，发送信号，使得界面上的slider一起变化

    def __init__(self):
        super().__init__()

        self.currentImgData = np.array([])

        # 创建image item , 用于显示图像
        self.imagePlot = self.addPlot(title="")  # 创建 imagePlot 用于plot图片
        self.imgItem = pg.ImageItem()  # 创建 imgItem
        self.imgItem.hoverEvent = self.imageHoverEvent  # 重写图片鼠标悬停事件
        self.imagePlot.setAutoVisible(y=True)

        # 创建hist item , 用于处理图像窗宽 窗高
        hist = pg.HistogramLUTItem()  # 创建 histogram
        hist.setImageItem(self.imgItem)  # 将 historgram 与 img item关联

        self.imagePlot.addItem(self.imgItem)  # 添加 imgItem到 p1 上
        self.addItem(hist)  # 窗口 win 上 添加hist

        # 创建pos label 显示鼠标在图像中的位置 及值
        self.posLabel = pg.LabelItem()

        # 创建image page label 用于显示当前图像的索引
        self.imagePageLabel = pg.LabelItem()

        # 图片处理区域布局
        self.addItem(self.posLabel, 0, 0, colspan=2)
        self.addItem(self.imagePageLabel, 0, 2)
        self.addItem(self.imagePlot, 1, 0, colspan=2)
        self.addItem(hist, 1, 2)

        # self.text1 = pg.TextItem("hello")
        # self.text1.setParentItem(self.img)
        # self.text1.setPos(200,200)

        # self.isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        # hist.vb.addItem(self.isoLine)
        # hist.vb.setMouseEnabled(y=False)  # makes user interaction a little easier
        # self.isoLine.setValue(0.8)
        # self.isoLine.setZValue(1000)
        #
        # self.iso = pg.IsocurveItem(level=0.8, pen='g')
        # self.iso.setParentItem(self.img)
        # self.iso.setZValue(5)
        #
        #
        #
        # self.isoLine.sigDragged.connect(self.updateIsocurve)

        self.viewBox = self.imagePlot.getViewBox()

        self.isCtrlPressed = False  # 判断是否按下了control键


    def updateIsocurve(self):
        self.iso.setLevel(self.isoLine.value())

    def initImage(self, data):
        """
        初始化 image , 当读取一组数据时, 将数据存入在 该类的 images变量内, 并显示第一章图

        :param data: 读取的图像数据
        :return:
        """
        self.currentImgData = data.T
        self.imgItem.setImage(self.currentImgData)


    def wheelEvent(self, ev):
        """
            切换图片 ctrl + wheel
            放大缩小 wheel
        :param ev:
        :return:
        """

        if self.isCtrlPressed:  # 切换图片 ctrl + wheel

            if self.images.shape[0] == 1:  # 说明只有一幅图
                return

            self.imagePageLabel.setText("{}/{}".format(self.image_index + 1, self.image_number))

            self.pageTurnSignal.emit(self.image_index)
            delta = ev.angleDelta().y()

            if delta > 0 and self.image_index < self.images.shape[0] - 1:
                self.image_index += 1

            elif delta < 0 and self.image_index > 0:

                self.image_index -= 1
            else:
                return

            self.update(self.images[self.image_index])

        else:  # 放大缩小

            super(ImageGraphicsLayoutWidget, self).wheelEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Control:
            self.isCtrlPressed = True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.isCtrlPressed = False

    def mouseMoveEvent(self, ev):

        pos = ev.pos()
        point1 = self.viewBox.mapFromView(QPoint(0,0)) #scene 到 view的点
        point2 = self.viewBox.mapToView(QPoint(0,0)) #view 到 scene的点
        rect = self.viewBox.viewRect() #返回view box在scene中的坐标以及长和宽

        print(rect)
        super(ImageGraphicsLayoutWidget, self).mouseMoveEvent(ev)

    def imageHoverEvent(self, event):
        """Show the position, pixel, and value under the mouse cursor.
        """
        if event.isExit():
            self.imagePlot.setTitle("")
            return

        pos = event.pos()
        i, j = pos.y(), pos.x()



        i = int(np.clip(i, 0, self.currentImgData.shape[0] - 1))
        j = int(np.clip(j, 0, self.currentImgData.shape[1] - 1))

        ppos = self.imgItem.mapToParent(pos)
        x, y = ppos.x(), ppos.y()
        val = self.currentImgData[j, i]

        self.posLabel.setText("pos: (%0.1f, %0.1f)  pixel: (%d, %d) value: %0.1f" % (x, y, i, j, val))

    def clearPlotItem(self):

        self.imagePlot.clear()

        self.imagePlot.addItem(self.imgItem)


class ImageQuanlityWidget(Ui_Form, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.imgWin = ImageGraphicsLayoutWidget()

        self.imageShowLayout.addWidget(self.imgWin)

        self.img = cv2.imread(r"F:\PythonProject\PyqtGrapyTest\lufei.jpg",0)

        self.imagePlot = self.imgWin.imagePlot

        self.imgWin.initImage(self.img)

        self.pushButton.clicked.connect(self.addRoi)

    def addRoi(self):


        roi = pg.CircleROI([80, 50], [20, 20], pen=(10, 9), removable=True, scaleSnap=True, translateSnap=True)

        self.imagePlot.addItem(roi)
        roi.setZValue(10)  # make sure ROI is drawn above image
        roi.setAcceptedMouseButtons(Qt.LeftButton)
        roi.sigClicked.connect(lambda: self.getMeanValInRoi(roi))
        roi.sigRemoveRequested.connect(lambda roi: self.removeRoi(roi))

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = ImageQuanlityWidget()
    MainWindow.show()
    sys.exit(app.exec_())
