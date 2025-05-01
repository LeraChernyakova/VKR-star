import numpy as np
import matplotlib.pyplot as plt

# Данные
objects = np.array([502, 125, 405, 282, 482, 102, 1086, 14])
times = np.array([4.5320, 0.1278, 3.1986, 1.9054, 4.3886, 0.6418, 11.2820, 0.0470])

# Построение точек
plt.scatter(objects, times, label='Измерения')

# Линейная регрессия для линии тренда
coeffs = np.polyfit(objects, times, 1)  # coeffs[0]=a, coeffs[1]=b
poly = np.poly1d(coeffs)

# Точки для линии тренда
x_line = np.linspace(objects.min(), objects.max(), 100)
plt.plot(x_line, poly(x_line), linestyle='--', color='red', label=f'Линейная аппроксимация')

# Настройки графика
plt.xlabel('Количество объектов на снимке, шт')
plt.ylabel('Время обработки, сек')
plt.grid(True)
plt.legend()

# Показать график
plt.show()