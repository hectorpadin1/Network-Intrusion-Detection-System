import gc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, KFold

import tensorflow as tf
import keras_tuner as kt
from tensorflow import keras


# PARÁMETROS PARA LA HYPERPARAMETRIZACIÓN

# Capas no profundas
INPUT = 22
OUTPUT = 7

# Capas
MAX_LAYERS = 6
MIN_LAYERS = 2

# Nodos
MAX_NODES = 512
MIN_NODES = 32
NODE_STEP = 32

# Dropout
MAX_DROPOUT = 0.3
MIN_DROPOUT = 0
DROPOUT_STEP = 0.1

# Learning rate
LR_VALUES = [1e-2, 1e-3, 1e-4]


class MyHyperModel(kt.HyperModel):
    
    def build(self, hp):
        model = keras.Sequential()
        model.add(keras.layers.Flatten(input_shape=(INPUT,)))
        
        # Capas ocultas: 2 - 6
        # Unidades: 32 a 512 en intervalos de 32
        for i in range(1, hp.Int("num_layers", MIN_LAYERS, MAX_LAYERS)):
            model.add(
                keras.layers.Dense(
                    units=hp.Int("units_" + str(i), min_value=MIN_NODES, max_value=MAX_NODES, step=NODE_STEP),
                    activation="relu")
            )
            # Capa de Dropout con valores de 0 a 0.3 en intervalos de 0.1.
            model.add(keras.layers.Dropout(hp.Float("dropout_" + str(i), MIN_DROPOUT, MAX_DROPOUT, step=DROPOUT_STEP)))

        # Capa de salida
        model.add(keras.layers.Dense(OUTPUT, activation="softmax"))
        
        # Hyperparametrización de learning rate
        hp_learning_rate = hp.Choice("learning_rate", values=LR_VALUES)
        model.compile(optimizer = keras.optimizers.Adam(learning_rate=hp_learning_rate),
                  loss = keras.losses.SparseCategoricalCrossentropy(),
                  metrics=["accuracy"])
    
        return model

    def fit(self, hp, model, *args, **kwargs):
        # Hyperparametrización del batch size
        return model.fit(
            *args,
            batch_size=hp.Choice("batch_size", [32, 64, 96, 128, 160]),
            **kwargs,
        )


class CVTuner(kt.engine.tuner.Tuner):
    
    # En cada trial, los modelos se evalúan con una 3-fold cross-validation
    def run_trial(self, trial, x, y, batch_size=32, epochs=1):
        # 3-fold cross-validation 
        cv = KFold(3)
        val_losses = []
        
        for train_indices, test_indices in cv.split(x):
            x_train, x_test = x[train_indices], x[test_indices]
            y_train, y_test = y[train_indices], y[test_indices]
            model = self.hypermodel.build(trial.hyperparameters)
            model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs)
            val_losses.append(model.evaluate(x_test, y_test))
        
        self.oracle.update_trial(trial.trial_id, {'val_loss': np.mean(val_losses)})
        self.save_model(trial.trial_id, model)

        
        
df = pd.read_csv('/home/jovyan/My-Notebooks/Data Preprocess/hyper-SD.csv', sep=',', low_memory=False)
y = df.pop('Label')
X = df.values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=100)

X_train = X_train.astype('float32')
X_test = X_test.astype('float32')

oracle = kt.oracles.BayesianOptimizationOracle(
    objective=None,
    max_trials=10,
    num_initial_points=None,
    alpha=0.0001,
    beta=2.6,
    seed=None,
    hyperparameters=None,
    allow_new_entries=True,
    tune_new_entries=True,
)

tuner = CVTuner(
    MyHyperModel(),
    oracle = oracle
)


stop_early = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)
tuner.search(X_train, y_train, epochs=20, validation_split=0.2, callbacks=[stop_early], verbose=2)

best_hps = tuner.get_best_hyperparameters()[0]
h_model = tuner.hypermodel.build(best_hps)

del(tuner, df, X_train, X_test, y_train, y_test, X, y)
gc.collect()


df = pd.read_csv('/home/jovyan/My-Notebooks/Data Preprocess/train-SD-reduced.csv', sep=',', low_memory=False)
y_train = df.pop('Label')
X_train = df.values

h_model.fit(X_train, y_train, epochs=500, shuffle=True, callbacks=[stop_early])

h_model.save('/home/jovyan/My-Notebooks/Signature Detection/dnn-hyper/')