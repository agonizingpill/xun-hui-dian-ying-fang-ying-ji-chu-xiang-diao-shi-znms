from functools import lru_cache
from random import Random

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

from domain.states import Artifact

FEATURES = ('edge_loss', 'color_error', 'flicker_index', 'frame_var')
MODEL_VERSION = 'ext-20261124-demo'
SWEEP_STEPS = 1000
CENTERS = {
    Artifact.CLEAN: (.10,.11,.10,.09),
    Artifact.SOFT: (.76,.12,.13,.19),
    Artifact.SHIFT: (.13,.77,.18,.20),
    Artifact.FLICKER: (.18,.15,.81,.70),
}


def simulated_data(seed, size):
    rng = Random(seed)
    rows, labels = [], []
    for label, center in CENTERS.items():
        for _ in range(size):
            rows.append([max(0,min(1,rng.gauss(mean, .065))) for mean in center])
            labels.append(str(label))
    return rows, labels


@lru_cache(maxsize=1)
def fitted():
    samples, labels = simulated_data(411, 55)
    check, known = simulated_data(276, 15)
    model = ExtraTreesClassifier(n_estimators=96,max_depth=7,min_samples_leaf=2,random_state=221,n_jobs=1)
    model.fit(samples,labels)
    predicted = model.predict(check)
    report = {'training':len(samples),'holdout':len(check),'accuracy':float(accuracy_score(known,predicted)),
              'labels': list(model.classes_), 'matrix':confusion_matrix(known,predicted,labels=model.classes_).tolist()}
    return model, report


def calculate(payload):
    model, report = fitted()
    sensors = payload['sensors']
    gaps = [field for field in FEATURES if sensors.get(field) is None]
    if len(gaps) > 1:
        raise ValueError('校准读数缺项超过一项，无法判别')
    if gaps:
        return sweep_missing(model, report, sensors, gaps[0])
    values = [[sensors[field] for field in FEATURES]]
    chances = model.predict_proba(values)[0].tolist()
    top = max(range(len(chances)), key=chances.__getitem__)
    return {'model_version': MODEL_VERSION, 'artifact': str(model.classes_[top]), 'probability': chances[top],
            'votes': dict(zip(model.classes_, chances, strict=True)), 'holdout': report}


def sweep_missing(model, report, sensors, field):
    """缺项按量程全程扫描：无论缺项取何值，都取最不利于签放的判别落库。"""
    grid = [step / SWEEP_STEPS for step in range(SWEEP_STEPS + 1)]
    rows = [[sensors[name] if name != field else point for name in FEATURES] for point in grid]
    matrix = model.predict_proba(rows)
    classes = list(model.classes_)
    clean = classes.index(str(Artifact.CLEAN))
    worst = min(range(len(grid)), key=lambda at: matrix[at][clean])
    chances = matrix[worst].tolist()
    top = max(range(len(chances)), key=chances.__getitem__)
    return {'model_version': MODEL_VERSION, 'artifact': str(classes[top]), 'probability': chances[top],
            'votes': dict(zip(classes, chances, strict=True)), 'holdout': report,
            'missing_field': field, 'swept': len(grid), 'clean_floor': chances[clean],
            'worst_reading': grid[worst]}
