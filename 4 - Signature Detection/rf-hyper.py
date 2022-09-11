import gc
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
from sklearn.metrics import make_scorer
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from joblib import dump


def plot_grid_search(cv_results, grid_param_1, grid_param_2, name_param_1, name_param_2):
    # Get Test Scores Mean and std for each grid search
    scores_mean = cv_results['mean_test_score']
    scores_mean = np.array(scores_mean).reshape(len(grid_param_2),len(grid_param_1))

    scores_sd = cv_results['std_test_score']
    scores_sd = np.array(scores_sd).reshape(len(grid_param_2),len(grid_param_1))

    # Plot Grid search scores""
    _, ax = plt.subplots(1,1)

    # Param1 is the X-axis, Param 2 is represented as a different curve (color line)
    for idx, val in enumerate(grid_param_2):
        ax.plot(grid_param_1, scores_mean[idx,:], '-o', label= name_param_2 + ': ' + str(val))

    ax.set_title("Grid Search Scores", fontsize=20, fontweight='bold')
    ax.set_xlabel(name_param_1, fontsize=16)
    ax.set_ylabel('CV Average Score', fontsize=16)
    ax.legend(loc="best", fontsize=15)
    ax.grid('on')
    plt.savefig('rf-hyper.png', dpi=100)


df = pd.read_csv('/home/jovyan/My-Notebooks/Data Preprocess/hyper-SD.csv', sep=',', low_memory=False)
y = df.pop('Label')
X = df.values

param_grid = {
    'max_features': ['auto', 2, 3, 5, 10, 20],
    'n_estimators': [100, 200, 500, 1000, 1500]
}
rf = RandomForestClassifier() # Instantiate the grid search model
grid_search = GridSearchCV(estimator = rf, param_grid = param_grid, cv = 3)
grid_search.fit(X, y)
print(grid_search.cv_results_)
plot_grid_search(grid_search.cv_results_, param_grid['max_features'], param_grid['n_estimators'], 'Max Features', 'Number of Estimators')


print("Accuracy score on Validation set: \n")
print(grid_search.best_score_ )
print("---------------")
print("Best performing hyperparameters on Validation set: ")
print(grid_search.best_params_)
print("---------------")
print(grid_search.best_estimator_)
RF = grid_search.best_estimator_


del(X, y)
gc.collect()

df = pd.read_csv('/home/jovyan/My-Notebooks/Data Preprocess/train-SD-reduced.csv', sep=',', low_memory=False)
y_train = df.pop('Label')
X_train = df.values

# Train the hypertuned model
RF.fit(X_train, y_train)

dump(RF, '/home/jovyan/My-Notebooks/Signature Detection/rf-hyper/RF.joblib')