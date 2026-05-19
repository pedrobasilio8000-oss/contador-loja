import cv2
from ultralytics import YOLO
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuração Google Sheets
CREDENCIAIS = "contador-loja-4768ab5770f4.json"
ID_PLANILHA = "1W_7Won4bMFdtFxm6gVsPcbO-9mcuXqutD9KdTmJrXD8"

def conectar_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(CREDENCIAIS, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(ID_PLANILHA).sheet1
    return sheet

def get_turno(hora):
    h = hora.hour
    if 6 <= h < 12:
        return "Manhã"
    elif 12 <= h < 18:
        return "Tarde"
    else:
        return "Noite"

def get_dia_semana(data):
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return dias[data.weekday()]

def registrar_passagem(sheet, id_pessoa):
    agora = datetime.now()
    sheet.append_row([
        agora.strftime("%d/%m/%Y"),
        agora.strftime("%H:%M:%S"),
        get_dia_semana(agora),
        get_turno(agora),
        id_pessoa
    ])

def main():
    print("Conectando ao Google Sheets...")
    sheet = conectar_sheets()
    print("Conectado! ✅")

    model = YOLO("yolo11n.pt")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: não foi possível acessar a webcam!")
        return

    contagem = 0
    ids_vistos = set()

    print("Sistema iniciado! Pressione 'Q' para encerrar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(frame, persist=True, classes=[0], verbose=False, tracker="bytetrack.yaml")

        if results[0].boxes is not None and results[0].boxes.id is not None:
            ids_atuais = results[0].boxes.id.int().tolist()
            boxes = results[0].boxes.xyxy.int().tolist()

            for i, id_pessoa in enumerate(ids_atuais):
                if id_pessoa not in ids_vistos:
                    ids_vistos.add(id_pessoa)
                    contagem += 1
                    registrar_passagem(sheet, id_pessoa)
                    print(f"Passagem registrada! ID:{id_pessoa} | Total: {contagem}")

                x1, y1, x2, y2 = boxes[i]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID:{id_pessoa}", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.putText(frame, f"Passagens: {contagem}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Visitantes estimados: {contagem // 2}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
        cv2.putText(frame, "Pressione Q para sair", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Contador de Pessoas", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nSistema encerrado. Total: {contagem} passagens | {contagem // 2} visitantes estimados")

if __name__ == "__main__":
    main()