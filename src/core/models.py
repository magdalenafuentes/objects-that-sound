from functools import reduce

from tensorflow.python.keras import Model, Sequential
from tensorflow.python.keras.activations import *
from tensorflow.python.keras.layers import *


class AVC:
    _vision_subnetwork = None
    _audio_subnetwork = None
    _fusion_subnetwork = None
    __model__ = None

    def get_model(self) -> Model:
        if self.__model__ is None:
            self.__model__ = self.__fuse__()
        return self.__model__

    @property
    def vision_subnetwork(self):
        if self._vision_subnetwork is None:
            raise NotImplementedError('\'vision subnetwork must be defined')
        return self._vision_subnetwork

    @property
    def audio_subnetwork(self):
        if self._audio_subnetwork is None:
            raise NotImplementedError('\'audio subnetwork must be defined')
        return self._audio_subnetwork

    @property
    def fusion_subnetwork(self):
        if self._fusion_subnetwork is None:
            raise NotImplementedError('\'fusion subnetwork must be defined')
        return self._fusion_subnetwork

    @property
    def vision_input_shape(self):
        return self.vision_subnetwork.input_shape[1:]

    @property
    def audio_input_shape(self):
        return self.audio_subnetwork.input_shape[1:]

    @property
    def input_shape(self):
        return [self.vision_input_shape, self.audio_input_shape]

    @property
    def output_shape(self):
        return self.get_model().output_shape[1:]

    def __fuse__(self):
        concat = [self.vision_subnetwork.output, self.audio_subnetwork.output]
        fusion = reduce(lambda x, f: f(x), self.fusion_subnetwork, concat)
        inputs = [self.vision_subnetwork.input, self.audio_subnetwork.input]
        return Model(inputs, fusion)


class L3Net(AVC):
    _vision_subnetwork = Sequential([
        InputLayer((224, 224, 3), name='vision_input'),

        Conv2D(64, 3, padding='same', activation=relu, name='vision_conv1_1'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation=relu, name='vision_conv1_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool1'),

        Conv2D(128, 3, padding='same', activation=relu, name='vision_conv2_1'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation=relu, name='vision_conv2_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool2'),

        Conv2D(256, 3, padding='same', activation=relu, name='vision_conv3_1'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation=relu, name='vision_conv3_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool3'),

        Conv2D(512, 3, padding='same', activation=relu, name='vision_conv4_1'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation=relu, name='vision_conv4_2'),
        BatchNormalization(),
        MaxPool2D(28, name='vision_pool4'),
        Flatten(name='vision_flatten')])

    _audio_subnetwork = Sequential([
        InputLayer((257, 199, 1), name='audio_input'),

        Conv2D(64, 3, padding='same', activation=relu, name='audio_conv1_1'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation=relu, name='audio_conv1_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool1'),

        Conv2D(128, 3, padding='same', activation=relu, name='audio_conv2_1'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation=relu, name='audio_conv2_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool2'),

        Conv2D(256, 3, padding='same', activation=relu, name='audio_conv3_1'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation=relu, name='audio_conv3_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool3'),

        Conv2D(512, 3, padding='same', activation=relu, name='audio_conv4_1'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation=relu, name='audio_conv4_2'),
        BatchNormalization(),
        MaxPool2D((32, 24), name='audio_pool4'),
        Flatten(name='audio_flatten')])

    _fusion_subnetwork = [
        Concatenate(name='concat'),
        Dense(128, name='fc1'),
        Dense(2, name='fc2'),
        Softmax(name='softmax')]


class AVENet(AVC):
    _vision_subnetwork = Sequential([
        InputLayer((224, 224, 3), name='vision_input'),

        Conv2D(64, 3, 2, padding='same', activation=relu, name='vision_conv1_1'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation=relu, name='vision_conv1_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool1'),

        Conv2D(128, 3, padding='same', activation=relu, name='vision_conv2_1'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation=relu, name='vision_conv2_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool2'),

        Conv2D(256, 3, padding='same', activation=relu, name='vision_conv3_1'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation=relu, name='vision_conv3_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool3'),

        Conv2D(512, 3, padding='same', activation=relu, name='vision_conv4_1'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation=relu, name='vision_conv4_2'),
        BatchNormalization(),
        MaxPool2D(14, name='vision_pool4'),

        Dense(128, name='vision_fc1'),
        Dense(128, name='vision_fc2'),
        Lambda(lambda x: K.l2_normalize(x), name='vision_L2_norm')])

    _audio_subnetwork = Sequential([
        InputLayer((257, 200, 1), name='audio_input'),

        Conv2D(64, 3, 2, padding='same', activation=relu, name='audio_conv1_1'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation=relu, name='audio_conv1_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool1'),

        Conv2D(128, 3, padding='same', activation=relu, name='audio_conv2_1'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation=relu, name='audio_conv2_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool2'),

        Conv2D(256, 3, padding='same', activation=relu, name='audio_conv3_1'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation=relu, name='audio_conv3_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool3'),

        Conv2D(512, 3, padding='same', activation=relu, name='audio_conv4_1'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation=relu, name='audio_conv4_2'),
        BatchNormalization(),
        MaxPool2D((16, 12), name='audio_pool4'),

        Dense(128, name='audio_fc1'),
        Dense(128, name='audio_fc2'),
        Lambda(lambda x: K.l2_normalize(x), name='audio_L2_norm')])

    _fusion_subnetwork = [
        Lambda(lambda x: K.sum(K.abs(x[0] - x[1]), axis=-1), name='euclidean_distance'),
        Dense(2, name='fc3'),
        Flatten(name='vision_flatten'),
        Softmax(name='softmax')]


class AVOLNet(AVC):
    _vision_subnetwork = Sequential([
        InputLayer((224, 224, 3), name='vision_input'),

        Conv2D(64, 3, 2, padding='same', activation=relu, name='vision_conv1_1'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation=relu, name='vision_conv1_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool1'),

        Conv2D(128, 3, padding='same', activation=relu, name='vision_conv2_1'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation=relu, name='vision_conv2_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool2'),

        Conv2D(256, 3, padding='same', activation=relu, name='vision_conv3_1'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation=relu, name='vision_conv3_2'),
        BatchNormalization(),
        MaxPool2D(2, name='vision_pool3'),

        Conv2D(512, 3, padding='same', activation=relu, name='vision_conv4_1'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation=relu, name='vision_conv4_2'),
        BatchNormalization(),
        Conv2D(128, 1, padding='same', activation=relu, name='vision_conv5'),
        BatchNormalization(),
        Conv2D(128, 1, padding='same', activation=relu, name='vision_conv6'),
        BatchNormalization()])

    _audio_subnetwork = Sequential([
        InputLayer((257, 200, 1), name='audio_input'),

        Conv2D(64, 3, 2, padding='same', activation=relu, name='audio_conv1_1'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation=relu, name='audio_conv1_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool1'),

        Conv2D(128, 3, padding='same', activation=relu, name='audio_conv2_1'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation=relu, name='audio_conv2_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool2'),

        Conv2D(256, 3, padding='same', activation=relu, name='audio_conv3_1'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation=relu, name='audio_conv3_2'),
        BatchNormalization(),
        MaxPool2D(2, name='audio_pool3'),

        Conv2D(512, 3, padding='same', activation=relu, name='audio_conv4_1'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation=relu, name='audio_conv4_2'),
        BatchNormalization(),
        MaxPool2D((16, 12), name='audio_pool4'),

        Dense(128, name='audio_fc1'),
        Dense(128, name='audio_fc2')])

    _fusion_subnetwork = [
        Lambda(lambda x: K.sum(x[0] * x[1], axis=-1, keepdims=True), name='scalar_products'),
        Conv2D(1, 1, padding='same', activation=relu, name='conv7'),
        BatchNormalization(),
        Lambda(lambda x: K.sigmoid(x), name='sigmoid'),
        MaxPool2D(14, name='maxpool'),
        Flatten()]