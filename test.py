#-*-coding:utf-8-*-
# 导入必要的软件包
import argparse
import datetime
import imutils
import time
import cv2
 
import threading
import yagmail
 
# 创建参数解析器并解析参数
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())
shot_idx = 0
# 如果video参数为None，那么我们从摄像头读取数据
if args.get("video", None) is None:
    camera = cv2.VideoCapture(0)#直接打开摄像头0获取图像
 
# 否则我们读取一个视频文件
else:
    camera = cv2.VideoCapture(args["video"])
 
 
 
 
def shijue() :
    shot_idx = 0
    # 遍历视频的每一帧
    # 初始化视频流的第一帧
    firstFrame = None
    while True:
 
        # 读入摄像头的帧
        (grabbed, frame) = camera.read()
        text = "Stop"
        flat = 0
        # 如果不能抓取到一帧，说明我们到了视频的结尾
        if not grabbed:
            break
        cv2.imshow('frame',frame)
        # 调整该帧的大小，转换为灰阶图像并且对其进行高斯模糊
        frame = imutils.resize(frame, width=500)
        # 对帧进行预处理，先转灰度图，再进行高斯滤波。
        # 用高斯滤波进行模糊处理，进行处理的原因：每个输入的视频都会因自然震动、光照变化或者摄像头本身等原因而产生噪声。对噪声进行平滑是为了避免在运动和跟踪时将其检测出来。
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        cv2.imshow('gray', gray)
        # 如果第一帧是None，对其进行初始化
 
        if firstFrame is None:
            firstFrame = gray#一开始检测的话首帧会不存在，那么就把灰度图作为首帧
            continue
        # 计算当前帧和第一帧的不同
        # 对于每个从背景之后读取的帧都会计算其与北京之间的差异，并得到一个差分图（different map）。
        # 还需要应用阈值来得到一幅黑白图像，并通过下面代码来膨胀（dilate）图像，从而对孔（hole）和缺陷（imperfection）进行归一化处理
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        firstFrame = gray
 
        # 扩展阀值图像填充孔洞，然后找到阀值图像上的轮廓
        thresh = cv2.dilate(thresh, None, iterations=2)
        # 搜索轮廓
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                                      cv2.CHAIN_APPROX_SIMPLE)
        #这里用的是opencv4，cv2.findContours返回了2个参数，但是用opencv3的话会返回3给参数，你要确保有足够的变量承接返回值可改成 binary, contours, hierarchy = cv.findContours(thresh, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        #返回值:contours:一个列表，每一项都是一个轮廓， 不会存储轮廓所有的点，只存储能描述轮廓的点hierarchy:一个ndarray, 元素数量和轮廓数量一样， 每个轮廓contours[i]对应4个hierarchy元素hierarchy[i][0] ~hierarchy[i][3]，分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号，如果没有对应项，则该值为负数
 
        """
            cv.findContours()
                参数：
                    1 要寻找轮廓的图像 只能传入二值图像，不是灰度图像
                    2 轮廓的检索模式，有四种：
                        cv2.RETR_EXTERNAL表示只检测外轮廓
                        cv2.RETR_LIST检测的轮廓不建立等级关系
                        cv2.RETR_CCOMP建立两个等级的轮廓，上面的一层为外边界，
                            里面的一层为内孔的边界信息。
                            如果内孔内还有一个连通物体，这个物体的边界也在顶层
                        cv2.RETR_TREE建立一个等级树结构的轮廓
                    3 轮廓的近似办法
                        cv2.CHAIN_APPROX_NONE存储所有的轮廓点，
                            相邻的两个点的像素位置差不超过1，
                            即max（abs（x1-x2），abs（y2-y1））==1
                        cv2.CHAIN_APPROX_SIMPLE压缩水平方向，垂直方向，对角线方向的元素，
                            只保留该方向的终点坐标，例如一个矩形轮廓只需4个点来保存轮廓信息
                返回值:
                    contours:一个列表，每一项都是一个轮廓， 不会存储轮廓所有的点，只存储能描述轮廓的点
                    hierarchy:一个ndarray, 元素数量和轮廓数量一样， 
                        每个轮廓contours[i]对应4个hierarchy元素hierarchy[i][0] ~hierarchy[i][3]，
                        分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号，如果没有对应项，则该值为负数
            """
        # 遍历轮廓
        for c in contours:
            # 轮廓太小忽略 有可能是斑点噪声
 
            if cv2.contourArea(c) < 5000:  # 该为args["min_area"]
                continue
            # 将轮廓画出来
            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            # 计算轮廓的边界框，在当前帧中画出该框
            flat = 1  # 设置一个标签，当有运动的时候为1
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Moving"
            # 在画面上显示运动
 
        # draw the text and timestamp on the frame
        # 在当前帧上写文字以及时间戳
        cv2.putText(frame, "Movement State: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
 
        # 显示当前帧并记录用户是否按下按键
 
        cv2.imshow("Thresh", thresh)
        cv2.imshow("Frame Delta", frameDelta)
        cv2.imshow("Security Feed", frame)
        #cv2.imwrite("/home/pi/Desktop/movement_detection/image.jpg", frame)#保存到某个位置，这里是树莓派
 
 
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 按q保存一张图片
            # cv2.imwrite("E:\cpy\pictures\\pic.jpg", frame1)
            break
 
    camera.release()
    cv2.destroyAllWindows()
 
 
def qqyouxian(num):#这里是控制邮箱发送的函数
    yag = yagmail.SMTP(user="*****@qq.com", password="****你的密码", host="smtp.exmail.qq.com")#这里应该填入你需要用的邮箱，user=邮箱地址，password=邮箱的密码，host=邮箱的服务器域名，这里是qq企业邮
    contents = ["检测到运动问物体", "/home/pi/Desktop/movement_detection/image.jpg"]#正文部分 随意，后面的是在树莓派系统下的抓拍地址，自己可以改一下
    # yag.send("w@qq.com", "检测到运动问物体", contents)#目标邮箱
    yag.close()
    
    time.sleep(50)
 
 
def main():#设计了多线程并行，邮件发送和机器视觉部分不冲突
    """创建启动线程"""
    t_sing = threading.Thread(target=shijue)
    t_dance = threading.Thread(target=qqyouxian, args=(6, ))
    t_sing.start()
    t_dance.start()
 
 
if __name__ == '__main__':
    main()