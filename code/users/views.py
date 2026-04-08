from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import UserRegistrationModel


def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            mobile = form.cleaned_data['mobile']
            loginid = form.cleaned_data['loginid']
            
            if UserRegistrationModel.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            elif UserRegistrationModel.objects.filter(mobile=mobile).exists():
                messages.error(request, 'Mobile number already exists.')
            elif UserRegistrationModel.objects.filter(loginid=loginid).exists():
                messages.error(request, 'Login ID already exists.')
            else:   
                form.save()
                messages.success(request, 'You have been successfully registered.')
                return redirect('UserLogin')
        else:
            print("FORM ERRORS:", form.errors)   
            messages.error(request, 'Form submission failed. Please check your inputs.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'userRegisterForm.html', {'form': form})


def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('username')
        pswd = request.POST.get('password')
        print("Login ID = ", loginid, ' Password = ', pswd)
        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            print(check.name)
            if check.status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                return render(request, 'users/userHome.html')
            else:
                messages.warning(request, 'Your account is not activated yet.')
        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'Invalid login ID or password.')
        except Exception as e:
            print('Exception occurred:', e)
            messages.error(request, 'An error occurred during login.')
    return render(request, 'userLogin.html')


def UserHome(request):
    return render(request, 'users/UserHome.html')


import os
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


def training(request):
    try:
        BASE_PATH = 'media\\ImagesOriginalSize'
        FOLDERS = {'NormalFinal': 1, 'ScolFinal': 2, 'SpondFinal': 3}

        image_data = []
        for folder_name, label in FOLDERS.items():
            folder_path = os.path.join(BASE_PATH, folder_name)
            if os.path.exists(folder_path):
                image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                for image_file in image_files:
                    full_path = os.path.join(folder_path, image_file)
                    image_data.append((full_path, label))

        data = pd.DataFrame(image_data, columns=['image_path', 'label'])

        X = data['image_path'].values.reshape(-1, 1)
        y = data['label'].values
        ros = RandomOverSampler(random_state=42)
        X_resampled, y_resampled = ros.fit_resample(X, y)

        balanced_data = pd.DataFrame({
            'image_path': X_resampled.flatten(),
            'label': y_resampled
        })

        train_data, temp_data = train_test_split(
            balanced_data, test_size=0.3,
            stratify=balanced_data['label'], random_state=42
        )

        valid_data, test_data = train_test_split(
            temp_data, test_size=0.5,
            stratify=temp_data['label'], random_state=42
        )

        for df in [train_data, valid_data, test_data]:
            df['label'] = df['label'].astype(str)

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

        model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        early_stop = EarlyStopping(patience=5, restore_best_weights=True)
        checkpoint = ModelCheckpoint("best_model.h5", save_best_only=True)

        history = model.fit(
            train_gen,
            validation_data=valid_gen,
            epochs=20,
            callbacks=[early_stop, checkpoint],
            verbose=1
        )

        loss, acc = model.evaluate(test_gen, verbose=0)
        return render(request,'users/training.html',{'loss':loss,"acc":acc})

    except Exception as e:
        return render(request,'users/training.html')


import numpy as np
from PIL import Image
from django.views.decorators.csrf import csrf_exempt
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from django.core.files.storage import default_storage

CLASS_LABELS = {0: 'NormalFinal', 1: 'ScolFinal', 2: 'SpondFinal'}


@csrf_exempt
def predict_image(request):
    try:
        if request.method == 'POST' and request.FILES.get('image'):
            image_file = request.FILES['image']

            image_path = default_storage.save('temp/' + image_file.name, image_file)
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)

            img = Image.open(full_path).convert('RGB')
            img = img.resize((128, 128))
            img_array = img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            model = load_model('best_model.h5')

            predictions = model.predict(img_array)
            predicted_index = np.argmax(predictions)
            predicted_label = CLASS_LABELS[predicted_index]
            confidence = float(predictions[0][predicted_index])

            os.remove(full_path)

            return render(request, 'users/prediction.html', {
                'prediction': predicted_label,
                'confidence': f"{confidence:.2f}"
            })
        else:
            return render(request, 'users/prediction.html')

    except Exception as e:
        return render(request, 'users/prediction.html')