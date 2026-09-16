import tensorflow as tf
import numpy as np


eye = tf.keras.models.load_model(
    "eye_model.keras"
)

yawn = tf.keras.models.load_model(
    "best_yawn_model.keras"
)


print("Eye:")
print(eye.input_shape)
print(eye.output_shape)

print("\nYawn:")
print(yawn.input_shape)
print(yawn.output_shape)


# completely black image
black = np.zeros(
    (1, 224, 224, 3),
    dtype=np.float32
)

# middle gray
gray = np.ones(
    (1, 224, 224, 3),
    dtype=np.float32
) * 127.5

# white
white = np.ones(
    (1, 224, 224, 3),
    dtype=np.float32
) * 255


print("\nEYE TEST")
print("black:", eye.predict(black, verbose=0))
print("gray :", eye.predict(gray, verbose=0))
print("white:", eye.predict(white, verbose=0))


print("\nYAWN TEST")
print("black:", yawn.predict(black, verbose=0))
print("gray :", yawn.predict(gray, verbose=0))
print("white:", yawn.predict(white, verbose=0))