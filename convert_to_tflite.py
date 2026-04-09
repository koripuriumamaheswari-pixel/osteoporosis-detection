import tensorflow as tf
import os

model_path = 'best_model.h5'
tflite_path = 'best_model.tflite'

print("Loading model...")
model = tf.keras.models.load_model(model_path)

print("Converting to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

print(f"Saving to {tflite_path}...")
with open(tflite_path, 'wb') as f:
    f.write(tflite_model)

print("Conversion complete!")
