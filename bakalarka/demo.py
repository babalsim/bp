from main import Program

if __name__ == '__main__':
    file = 'demo_dataset/titanic_zaciatok.MOV'
    y_start, y_end = 159, 284
    x_start, x_end = 13, 606
    c_x, c_y = 240, 97
    timeInSec = 2
    demoData = file, y_start, y_end, x_start, x_end, c_x, c_y, timeInSec
    Program(True, demoData)
