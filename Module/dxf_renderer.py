#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy as np
from random import randint

from Config.configs import CONFIG_COLLECTION

from Data.shape import Point

from Method.labels import getShapeListDictWithLabel

from Module.dxf_loader import DXFLoader

class DXFRenderer(DXFLoader):
    def __init__(self, config):
        super(DXFRenderer, self).__init__(config)
        self.line_color = [0, 255, 0]
        self.circle_color = [0, 255, 255]
        self.arc_color = [0, 0, 255]

        self.line_color = [255, 255, 255]
        self.circle_color = [255, 255, 255]
        self.arc_color = [255, 255, 255]

        self.image_width = None
        self.image_height = None
        self.free_width = None
        self.is_reverse_y = None

        self.trans_point = None
        self.scale = None

        self.render_image_width = None
        self.render_image_height = None

        self.image = None

        self.setImageSize(self.config['image_width'],
                          self.config['image_height'],
                          self.config['free_width'],
                          self.config['is_reverse_y'])
        return

    def setImageSize(self,
                     image_width,
                     image_height,
                     free_width,
                     is_reverse_y=False):
        if image_width <= 2 * free_width or image_height <= 2 * free_width:
            print("[ERROR][DXFRenderer::setImageSize]")
            print("\t free_width out of range!")
            return False
        self.image_width = image_width
        self.image_height = image_height
        self.free_width = free_width
        self.is_reverse_y = is_reverse_y
        return True

    def updateImageTrans(self):
        min_point = self.bbox.min_point
        self.trans_point = Point(-min_point.x, -min_point.y, -min_point.z)

        self.scale = float("inf")
        render_scale = float("inf")
        diff_point = self.bbox.diff_point
        if diff_point.x > 0:
            self.scale = min(self.scale,
                             1.0 * (self.image_width - 2.0 * self.free_width) / diff_point.x)
            render_scale = min(render_scale, 1.0 * self.image_width / diff_point.x)
        if diff_point.y > 0:
            self.scale = min(self.scale,
                             1.0 * (self.image_height - 2.0 * self.free_width) / diff_point.y)
            render_scale = min(render_scale, 1.0 * self.image_height / diff_point.y)

        if self.scale == float("inf"):
            self.scale = 1.0
        if render_scale == float("inf"):
            render_scale = 1.0

        self.render_image_width = int(diff_point.x * render_scale)
        self.render_image_height = int(diff_point.y * render_scale)
        return True

    def getImagePosition(self, world_potision):
        image_position = Point(
            int(self.free_width + (world_potision.x + self.trans_point.x) * self.scale),
            int(self.free_width + (world_potision.y + self.trans_point.y) * self.scale),
            int(self.free_width + (world_potision.z + self.trans_point.z) * self.scale))

        if self.is_reverse_y:
            image_position.y = self.render_image_height - image_position.y
        return image_position

    def getWorldPosition(self, image_position):
        if self.is_reverse_y:
            image_position.y = self.render_image_height - image_position.y

        world_potision = Point(
            1.0 * (image_position.x - self.free_width) / self.scale - self.trans_point.x,
            1.0 * (image_position.y - self.free_width) / self.scale - self.trans_point.y,
            1.0 * (image_position.z - self.free_width) / self.scale - self.trans_point.z)
        return world_potision

    def drawPoint(self, point , color):
        point_in_image = self.getImagePosition(point)
        cv2.circle(self.image,
                   (point_in_image.x, point_in_image.y),
                   1,
                   np.array(color, dtype=np.float) / 255.0,
                   4)
        return True

    def drawLine(self, line, color):
        start_point_in_image = self.getImagePosition(line.start_point)
        end_point_in_image = self.getImagePosition(line.end_point)
        cv2.line(self.image,
                 (start_point_in_image.x, start_point_in_image.y),
                 (end_point_in_image.x, end_point_in_image.y),
                 np.array(color, dtype=np.float) / 255.0,
                 1, 4)
        return True

    def drawCircle(self, circle, color):
        center_in_image = self.getImagePosition(circle.center)
        radius_in_image = int(circle.radius * self.scale)
        cv2.circle(self.image,
                   (center_in_image.x, center_in_image.y),
                   radius_in_image,
                   np.array(color, dtype=np.float) / 255.0,
                   1, 8, 0)
        return True

    def drawArc(self, arc, color):
        point_list = arc.flatten_point_list
        for i in range(len(point_list) - 1):
            current_point = point_list[i]
            next_point = point_list[i + 1]
            current_point_in_image = self.getImagePosition(current_point)
            next_point_in_image = self.getImagePosition(next_point)
            cv2.line(self.image,
                     (current_point_in_image.x, current_point_in_image.y),
                     (next_point_in_image.x, next_point_in_image.y),
                     np.array(color, dtype=np.float) / 255.0,
                     1, 4)
        return True

    def drawPointList(self, point_list, color):
        for point in point_list:
            self.drawPoint(point , color)
        return True

    def drawLineList(self, line_list, color):
        for line in line_list:
            self.drawLine(line, color)
        return True

    def drawLineLabel(self, label, color=None):
        value_color_dict = {}
        for line in self.line_list:
            value = line.getLabel(label)
            if value is None:
                continue
            if color is None:
                if value not in value_color_dict.keys():
                    random_color = [randint(0, 255),
                                    randint(0, 255),
                                    randint(0, 255)]
                    value_color_dict[value] = random_color
                color = value_color_dict[value]
            self.drawLine(line, color)
        return True

    def drawCircleList(self, circle_list, color):
        for circle in circle_list:
            self.drawCircle(circle, color)
        return True

    def drawArcList(self, arc_list, color):
        for arc in arc_list:
            self.drawArc(arc, color)
        return True

    def drawLineLabel(self, label, color=None):
        line_label_dict = getShapeListDictWithLabel(self.line_list, label)
        for _, line_list in line_label_dict.items():
            current_color = [randint(0, 255), randint(0, 255), randint(0, 255)]
            if color is not None:
                current_color = color
            self.drawLineList(line_list, current_color)
        return True

    def drawCircleLabel(self, label, color=None):
        circle_label_dict = getShapeListDictWithLabel(self.circle_list, label)
        for _, circle_list in circle_label_dict.items():
            current_color = [randint(0, 255), randint(0, 255), randint(0, 255)]
            if color is not None:
                current_color = color
            self.drawCircleList(circle_list, current_color)
        return True

    def drawArcLabel(self, label, color=None):
        arc_label_dict = getShapeListDictWithLabel(self.arc_list, label)
        for _, arc_list in arc_label_dict.items():
            current_color = [randint(0, 255), randint(0, 255), randint(0, 255)]
            if color is not None:
                current_color = color
            self.drawArcList(arc_list, current_color)
        return True

    def drawShape(self):
        self.drawLineList(self.line_list, self.line_color)
        self.drawCircleList(self.circle_list, self.circle_color)
        self.drawArcList(self.arc_list, self.arc_color)
        return True

    def render(self):
        self.updateImageTrans()
        self.image = np.zeros((self.render_image_height, self.render_image_width, 3))

        if not self.drawShape():
            print("[ERROR][DXFRenderer::render]")
            print("\t drawShape failed!")
            return False

        cv2.imshow(self.config['window_name'], self.image)
        return True

def demo():
    config = CONFIG_COLLECTION['render_all']

    dxf_renderer = DXFRenderer(config)
    dxf_renderer.outputInfo()
    dxf_renderer.render()
    cv2.waitKey(0)
    return True

if __name__ == "__main__":
    demo()

