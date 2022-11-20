import io

import cv2
import numpy as np
from PIL import Image
from tensorflow import keras

from .cyclegan.utils import ReflectionPadding2D


def binary2array(img_binary):
    stream = img_binary.stream.read()
    png = np.frombuffer(stream, dtype=np.uint8)
    img_array = cv2.imdecode(png, cv2.IMREAD_COLOR)[:, :, ::-1]
    return img_array


def generate_face(img_binary, img_size=(200, 200)):
    img_array = binary2array(img_binary)

    img_shape = img_array.shape
    height, width = img_shape[0], img_shape[1]

    cut_index1 = (width - height) // 2
    cut_index2 = (width + height) // 2

    img_array = img_array[:, cut_index1:cut_index2]
    img_resized = cv2.resize(img_array, img_size)

    img_normalized = (img_resized.astype(np.float32) / 127.5) - 1.0
    img_normalized = img_normalized[np.newaxis, :, :, :]

    model = keras.models.load_model(
        "apps/vanishingmask/checkpoints/mask2face_2.h5",
        custom_objects={"ReflectionPadding2D": ReflectionPadding2D},
    )

    model.summary()

    gen_face_array = model(img_normalized, training=False)[0].numpy()
    gen_face_array_resize = cv2.resize(gen_face_array, (height, height))
    gen_face_array = np.append(
        np.ones((height, cut_index1, 3)), gen_face_array_resize, axis=1
    )
    gen_face_array = np.append(gen_face_array, np.ones((height, cut_index1, 3)), axis=1)

    img_buffer = io.BytesIO()
    face_img = (gen_face_array * 127.5 + 127.5).astype(np.uint8)
    Image.fromarray(face_img).save(img_buffer, format="PNG")
    face_png = img_buffer.getvalue()

    return face_png
