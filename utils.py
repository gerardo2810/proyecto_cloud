# utils.py

def solicitar_numero(mensaje, minimo=1):
    while True:
        try:
            valor = int(input(mensaje))
            if valor >= minimo:
                return valor
            else:
                print(f"Debe ser un número mayor o igual a {minimo}.")
        except ValueError:
            print("Entrada inválida, ingrese un número.")

def solicitar_opcion(mensaje, opciones):
    while True:
        opcion = input(mensaje)
        if opcion in opciones:
            return opcion
        else:
            print(f"Opción inválida. Opciones válidas: {', '.join(opciones)}")
