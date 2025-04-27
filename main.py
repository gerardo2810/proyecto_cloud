# main.py

from topology_manager import crear_topologia, listar_topologias, borrar_topologia, unir_topologias

def menu_principal():
    while True:
        print("\n🌟 PUCPDEPLOY - GESTOR DE TOPOLOGÍAS 🌟")
        print("1. Crear nueva topología")
        print("2. Listar topologías")
        print("3. Borrar topología")
        print("4. Unir topologías")
        print("5. Salir")

        opcion = input("> ")

        if opcion == "1":
            crear_topologia()
        elif opcion == "2":
            listar_topologias()
        elif opcion == "3":
            borrar_topologia()
        elif opcion == "4":
            unir_topologias()
        elif opcion == "5":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("⚠️ Opción inválida.")

if __name__ == "__main__":
    menu_principal()
