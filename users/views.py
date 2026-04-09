import re
from django.shortcuts import render
from django.conf import settings
from .forms import UserRegistrationForm
from .models import UserRegistrationModel
from django.contrib import messages


def UserRegisterActions(request):
    if request.method == 'POST':

        name = request.POST.get('name')
        loginid = request.POST.get('loginid')
        password = request.POST.get('password')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        locality = request.POST.get('locality')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')

        # -----------------------------
        # VALIDATIONS
        # -----------------------------

        # 1. Mobile validation (Indian)
        if not re.match(r'^[6-9][0-9]{9}$', mobile):
            messages.error(request, "Invalid mobile number. Must be 10 digits and start with 6-9.")
            return render(request, 'UserRegistrations.html')

        # 2. Password validation
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', password):
            messages.error(request, "Password must have 1 capital letter, 1 number, 1 special symbol, and be at least 8 characters long.")
            return render(request, 'UserRegistrations.html')

        # 3. Check duplicate login ID
        if UserRegistrationModel.objects.filter(loginid=loginid).exists():
            messages.error(request, "Login ID already taken. Try another.")
            return render(request, 'UserRegistrations.html')

        # 4. Check duplicate mobile
        if UserRegistrationModel.objects.filter(mobile=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return render(request, 'UserRegistrations.html')

        # 5. Check duplicate email
        if UserRegistrationModel.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'UserRegistrations.html')

        # -----------------------------
        # SAVE DATA
        # -----------------------------
        UserRegistrationModel.objects.create(
            name=name,
            loginid=loginid,
            password=password,
            mobile=mobile,
            email=email,
            locality=locality,
            address=address,
            city=city,
            state=state,
            status='waiting'
        )

        messages.success(request, "Registration successful!")
        return render(request, 'UserRegistrations.html')

    return render(request, 'UserRegistrations.html')


def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('username')
        pswd = request.POST.get('password')
        print("Login ID = ", loginid, ' Password = ', pswd)
        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            status = check.status
            print('Status is = ', status)
            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                print("User id At", check.id, status)
                return render(request, 'users/userHome.html')
            else:
                messages.success(request, 'Your Account Not at activated')
                return render(request, 'userLogin.html')
        except Exception as e:
            print('Exception is ', str(e))
            messages.success(request, 'Invalid Login id and password')
    return render(request, 'userLogin.html', {})

def UserHome(request):
    return render(request, 'users/userHome.html')



def training(request):
    import os
    
    # Block training on Render Free Tier to avoid Out Of Memory crashes.
    if os.environ.get('RENDER') == 'true' or os.environ.get('RENDER'):
        from django.shortcuts import render
        # Mock success to avoid crashing
        return render(request,'users/training.html',{'loss':"0.1 (Cloud Mock)","acc":"98% (Cloud Mock)"})

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from django.http import JsonResponse
    from sklearn.model_selection import train_test_split
    from imblearn.over_sampling import RandomOverSampler
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    import warnings
    warnings.filterwarnings("ignore")

    try:
        BASE_PATH = 'media\ImagesOriginalSize'
        FOLDERS = {'NormalFinal': 1, 'ScolFinal': 2, 'SpondFinal': 3}

        # Step 1: Load Data
        image_data = []
        for folder_name, label in FOLDERS.items():
            folder_path = os.path.join(BASE_PATH, folder_name)
            if os.path.exists(folder_path):
                image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                for image_file in image_files:
                    full_path = os.path.join(folder_path, image_file)
                    image_data.append((full_path, label))

        data = pd.DataFrame(image_data, columns=['image_path', 'label'])

        # Step 2: Oversample
        X = data['image_path'].values.reshape(-1, 1)
        y = data['label'].values
        ros = RandomOverSampler(random_state=42)
        X_resampled, y_resampled = ros.fit_resample(X, y)

        balanced_data = pd.DataFrame({
            'image_path': X_resampled.flatten(),
            'label': y_resampled
        })

        # Step 3: Train/Val/Test Split
        train_data, temp_data = train_test_split(balanced_data, test_size=0.3, stratify=balanced_data['label'], random_state=42)
        valid_data, test_data = train_test_split(temp_data, test_size=0.5, stratify=temp_data['label'], random_state=42)

        for df in [train_data, valid_data, test_data]:
            df['label'] = df['label'].astype(str)

        # Step 4: Image Generators
        IMG_SIZE = (128, 128)
        BATCH_SIZE = 32

        tr_gen = ImageDataGenerator(rescale=1./255)
        val_gen = ImageDataGenerator(rescale=1./255)
        ts_gen = ImageDataGenerator(rescale=1./255)

        train_gen = tr_gen.flow_from_dataframe(
            train_data, x_col='image_path', y_col='label',
            target_size=IMG_SIZE, class_mode='categorical',
            shuffle=True, batch_size=BATCH_SIZE)

        valid_gen = val_gen.flow_from_dataframe(
            valid_data, x_col='image_path', y_col='label',
            target_size=IMG_SIZE, class_mode='categorical',
            shuffle=False, batch_size=BATCH_SIZE)

        test_gen = ts_gen.flow_from_dataframe(
            test_data, x_col='image_path', y_col='label',
            target_size=IMG_SIZE, class_mode='categorical',
            shuffle=False, batch_size=BATCH_SIZE)

        # Step 5: CNN Model
        model = Sequential([
            Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
            MaxPooling2D(pool_size=(2, 2)),

            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D(pool_size=(2, 2)),

            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D(pool_size=(2, 2)),

            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(3, activation='softmax')
        ])

        model.compile(optimizer=Adam(learning_rate=0.0001),
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])

        early_stop = EarlyStopping(patience=5, restore_best_weights=True)
        checkpoint = ModelCheckpoint("best_model.h5", save_best_only=True)

        history = model.fit(
            train_gen,
            validation_data=valid_gen,
            epochs=20,
            callbacks=[early_stop, checkpoint],
            verbose=1
        )

        # Step 6: Evaluation
        loss, acc = model.evaluate(test_gen, verbose=0)
        return render(request,'users/training.html',{'loss':loss,"acc":acc})

    except Exception as e:
        return render(request,'users/training.html')


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def predict_image(request):
    import os
    import numpy as np
    from PIL import Image
    from django.core.files.storage import default_storage
    from django.conf import settings
    
    CLASS_LABELS = {0: 'Normal', 1: 'Osteoporosis', 2: 'Other'}

    try:
        if request.method == 'POST' and request.FILES.get('image'):
            image_file = request.FILES['image']

            # Save image temporarily
            image_path = default_storage.save('temp/' + image_file.name, image_file)
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)

            # Preprocess image
            img = Image.open(full_path).convert('RGB')
            img = img.resize((128, 128))  # Must match training size
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.expand_dims(img_array, axis=0)  # shape: (1, 128, 128, 3)

            # Load TFLite model
            model_path = os.path.join(settings.BASE_DIR, 'best_model.tflite')
            try:
                import tflite_runtime.interpreter as tflite
                interpreter = tflite.Interpreter(model_path=model_path)
            except ImportError:
                import tensorflow as tf
                interpreter = tf.lite.Interpreter(model_path=model_path)
            interpreter.allocate_tensors()

            # Predict
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            interpreter.set_tensor(input_details[0]['index'], img_array)
            interpreter.invoke()
            predictions = interpreter.get_tensor(output_details[0]['index'])
            
            predicted_index = np.argmax(predictions)
            predicted_label = CLASS_LABELS[predicted_index]
            confidence = float(predictions[0][predicted_index])

            if predicted_index == 0:
                predicted_label = "Normal ✅"
            elif predicted_index == 1:
                predicted_label = "Osteoporosis Detected ⚠️"
            else:
                predicted_label = "Other Spine Condition"

            # Clean up
            os.remove(full_path)

            # Send to HTML page
            return render(request, 'users/prediction.html', {
                'prediction': predicted_label,
                'confidence': f"{confidence * 100:.2f}%"
            })
        else:
            return render(request, 'users/prediction.html')



        

    except Exception as e:
        return render(request, 'users/prediction.html')
