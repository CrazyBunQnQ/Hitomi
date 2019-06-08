import cv2
import colorList

filename = './test/004.jpg'


# 判断图片主要颜色
def get_main_color(file_full_name):
    frame = cv2.imread(file_full_name)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    maxsum = -100
    color = None
    color_dict = colorList.getColorList()
    for d in color_dict:
        mask = cv2.inRange(hsv, color_dict[d][0], color_dict[d][1])
        binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
        binary = cv2.dilate(binary, None, iterations=2)
        img, cnts, hiera = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sum = 0
        for c in cnts:
            sum += cv2.contourArea(c)
        # print("%s: %s" % (d, str(sum)))
        # if len(cnts) > 0:
        #     cv2.imwrite('./output/' + d + '.jpg', mask)
        if sum > maxsum:
            maxsum = sum
            color = d

    return color


# 获取颜色组成
def get_color_structure(filename):
    frame = cv2.imread(filename)
    arr = []
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    min_count = 10000
    color_dict = colorList.getColorList()
    for d in color_dict:
        mask = cv2.inRange(hsv, color_dict[d][0], color_dict[d][1])
        binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
        binary = cv2.dilate(binary, None, iterations=2)
        # img, cnts, hiera = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts, hiera = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sum = 0
        for c in cnts:
            sum += cv2.contourArea(c)
        # print("%s: %s" % (d, str(sum)))
        # if len(cnts) > 0:
        #     cv2.imwrite('./output/' + d + '.jpg', mask)
        if sum > min_count:
            arr.append(d)
    return arr


if __name__ == '__main__':
    print(get_main_color(filename))
    print(len(get_color_structure(filename)))
