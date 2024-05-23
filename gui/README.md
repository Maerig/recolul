# Recolul GUI

https://doc.qt.io/qtforpython-6/index.html

## Build

(In recolul root folder)

```
pyside6-deploy -c pysidedeploy.spec gui/main.py
```

## Regenerate icon resources

```
pyside6-rcc icons.qrc -o rc_icons.py
```
