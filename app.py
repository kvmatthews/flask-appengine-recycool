from flask import Flask, request, jsonify, make_response
import numpy as np
from keras.models import load_model
from datetime import datetime
import uuid
from PIL import Image
import io


# Model to Use
classification_result = []
model_path = './models/MulticlassRecycool.h5'
loaded_model = load_model(model_path)


# create flask app
app = Flask(__name__)

# Function to validate UUID
def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


# Building API
@app.route('/')
def index():
    if classification_result:
        return jsonify(classification_result)
    else:
        return jsonify({"message": "No predictions available."})


# Building API
@app.route('/recycool', methods=['GET', 'POST'])
def recycool():
    if request.method == 'GET':
        if classification_result:
            response = {
                'status': 'Success',
                'data': classification_result
            }
            return make_response(jsonify(response), 200)
        else:
            error_response = {
                'status': 'ERROR 404',
                'message': 'No data available'
            }
            return make_response(jsonify(error_response), 404)
    elif request.method == 'POST':
        try:
            # Error Handling
            if 'file' not in request.files:
                error_response = {
                    'status': 'ERROR',
                    'message': 'No file request'
                }
                return make_response(jsonify(error_response), 400)

            file = request.files['file']
            if file.filename == '':
                error_response = {
                    'status': 'ERROR',
                    'message': 'No selected file'
                }
                return make_response(jsonify(error_response), 400)

            allowed_extensions = {'png', 'jpg', 'jpeg'}
            if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                error_response = {
                    'status': 'ERROR',
                    'message': 'Invalid file format. Please upload an image (PNG, JPG, JPEG)'
                }
                return make_response(jsonify(error_response), 400)

            # Processing Logic
            img = Image.open(io.BytesIO(file.read()))
            img_rgb = img.convert('RGB')
            img_resized = img_rgb.resize((256, 256))
            img_array = np.array(img_resized) / 255.0
            img_normalized = np.expand_dims(img_array, axis=0)

            prediction = loaded_model.predict(img_normalized)
            predicted_class_index = np.argmax(prediction)
            accuracy = np.max(prediction)

            class_names = ['Kaca', 'Kardus', 'Kertas', 'Organik', 'Plastik']
            classification = class_names[predicted_class_index]

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            unique_id = str(uuid.uuid4())

            classification_data = {
                'ID': unique_id,
                'classification': classification,
                'accuracy': float(accuracy),
                'insertedAt': timestamp
            }

            classification_result.append(classification_data)

            response = {
                'status': 'success',
                'message': 'Image upload successfully'
            }

            return make_response(jsonify(response), 201)

        except Exception as e:
            error_response = {
                'status': 'ERROR 400',
                'message': 'Failed to upload image'
            }
            return make_response(jsonify(error_response), 400)

# Get Method by ID
@app.route('/recycool/<string:unique_id>', methods=['GET'])
def get_prediction(unique_id):
    if not is_valid_uuid(unique_id):
        error_response = {
            'status': 'ERROR 400',
            'message': 'Invalid ID format'
        }
        return make_response(jsonify(error_response), 400)

    found = False
    for prediction in classification_result:
        if prediction['ID'] == unique_id:
            found = True
            response = {
                'status': 'Success',
                'data': prediction
            }
            return make_response(jsonify(response), 200)
    
    if not found:
        error_response = {
            'status': 'ERROR 404',
            'message': 'Not found for the given ID'
        }
        return make_response(jsonify(error_response), 404)


# Delete Method
@app.route('/recycool/<string:unique_id>', methods=['DELETE'])
def delete_prediction(unique_id):
    global classification_result

    initial_length = len(classification_result)
    classification_result = [prediction for prediction in classification_result if prediction['ID'] != unique_id]
    final_length = len(classification_result)

    if final_length < initial_length:
        response = {
            'status': 'Success',
            'message': 'Deleted successfully'
        }
        return make_response(jsonify(response), 200)
    else:
        error_response = {
            'status': 'ERROR 404',
            'message': 'Not found for the given ID'
        }
        return make_response(jsonify(error_response), 404)


# Run flask server
if __name__ == '__main__':
    app.run(debug=True)
    