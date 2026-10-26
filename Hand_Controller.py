import cv2
import numpy as np
import pyautogui
import math
import time
import winsound
import sys
from cvzone.HandTrackingModule import HandDetector

# 1. GÜVENLİK ÖNLEMİ: Failsafe kapalıysa da kilitlenmeyi önleriz
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

print("[SYSTEM] Starting AI Hand Controller V1.0...")

# 2. GÜVENLİK ÖNLEMİ: Kamera Erişim Kontrolü
kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not kamera.isOpened():
    print("[ERROR] Camera is in use by another app or cannot be found!")
    print("[SYSTEM] Shutting down safely.")
    time.sleep(3)
    sys.exit()

kamera.set(3, 640)
kamera.set(4, 480)

print("[INFO] Camera initialized successfully.")

dedektor = HandDetector(maxHands=1, detectionCon=0.7)
ekran_genislik, ekran_yukseklik = pyautogui.size()
print(f"[INFO] Screen Resolution mapped to: {ekran_genislik}x{ekran_yukseklik}")

cerceve_boslugu = 120
onceki_x, onceki_y = 0, 0
son_tiklama_zamani = 0
son_sag_tiklama_zamani = 0
kaydirma_onceki_y = 0

sistem_aktif = True
surukleniyor = False
guncel_mod = "INITIALIZING"
onceki_mod = ""

hud_baslangic = None
kilit_hazir = True
HUD_KILIT_SURESI = 3.0
gecmis_zaman = time.time()


def parmak_acik_mi(noktalar, uc_id, eklem_id, taban_id=0):
    uc = noktalar[uc_id]
    eklem = noktalar[eklem_id]
    taban = noktalar[taban_id]
    uc_mesafe = math.hypot(uc[0] - taban[0], uc[1] - taban[1])
    eklem_mesafe = math.hypot(eklem[0] - taban[0], eklem[1] - taban[1])
    return uc_mesafe > eklem_mesafe * 1.05


try:
    while True:
        basarili, kare = kamera.read()
        if not basarili:
            print("[ERROR] Failed to grab frame from camera.")
            break

        kare = cv2.flip(kare, 1)

        cv2.rectangle(kare, (0, 0), (cerceve_boslugu, cerceve_boslugu), (0, 255, 255), 2)
        cv2.putText(kare, "LOCK", (35, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        eller, kare = dedektor.findHands(kare, draw=False)

        if eller:
            el = eller[0]
            noktalar = el["lmList"]
            acik_parmaklar = dedektor.fingersUp(el)

            bas_x, bas_y = noktalar[4][0], noktalar[4][1]
            isaret_x, isaret_y = noktalar[8][0], noktalar[8][1]
            orta_x, orta_y = noktalar[12][0], noktalar[12][1]
            serce_x, serce_y = noktalar[20][0], noktalar[20][1]

            if parmak_acik_mi(noktalar, 8, 6): acik_parmaklar[1] = 1
            if parmak_acik_mi(noktalar, 12, 10): acik_parmaklar[2] = 1

            mesafe_pinch = math.hypot(bas_x - isaret_x, bas_y - isaret_y)
            el_dik_mi = noktalar[0][1] > noktalar[9][1]

            if mesafe_pinch < 40 and el_dik_mi:
                acik_parmaklar[1] = 1

            guncel_zaman = time.time()

            # --- LOCK MECHANISM ---
            kilit_bolgesi_mi = (isaret_x < cerceve_boslugu and isaret_y < cerceve_boslugu)

            if kilit_bolgesi_mi:
                # GÜNCELLEME: Sistem uyuyorsa UNLOCKING, uyanıksa LOCKING yazar.
                guncel_mod = "LOCKING..." if sistem_aktif else "UNLOCKING..."

                if hud_baslangic is None:
                    hud_baslangic = guncel_zaman

                sure = guncel_zaman - hud_baslangic
                ilerleme = min(sure / HUD_KILIT_SURESI, 1.0)

                cv2.circle(kare, (isaret_x, isaret_y), int(15 + 30 * ilerleme), (0, 0, 255), 3)

                if sure >= HUD_KILIT_SURESI and kilit_hazir:
                    sistem_aktif = not sistem_aktif
                    kilit_hazir = False

                    if not sistem_aktif and surukleniyor:
                        pyautogui.mouseUp()
                        surukleniyor = False
                        print("[SYSTEM] Force MouseUp triggered by SLEEP MODE")

                    winsound.Beep(800, 200) if sistem_aktif else winsound.Beep(400, 400)
                    print(f"[STATE] System is now {'AWAKE' if sistem_aktif else 'ASLEEP'}")
            else:
                hud_baslangic = None
                kilit_hazir = True

                # --- STATE MACHINE ---
            if sistem_aktif and not kilit_bolgesi_mi:
                cv2.rectangle(kare, (cerceve_boslugu, cerceve_boslugu), (640 - cerceve_boslugu, 480 - cerceve_boslugu),
                              (255, 0, 255), 2)

                if surukleniyor or acik_parmaklar[1:5] == [1, 0, 0, 0] or acik_parmaklar[1:5] == [1, 0, 0, 1]:
                    hedef_x = np.interp(isaret_x, [cerceve_boslugu, 640 - cerceve_boslugu], [0, ekran_genislik])
                    hedef_y = np.interp(isaret_y, [cerceve_boslugu, 480 - cerceve_boslugu], [0, ekran_yukseklik])

                    hareket_hizi = math.hypot(hedef_x - onceki_x, hedef_y - onceki_y)
                    dinamik_yumusatma = 2 if hareket_hizi > 80 else (4 if hareket_hizi > 30 else 7)

                    guncel_x = onceki_x + (hedef_x - onceki_x) / dinamik_yumusatma
                    guncel_y = onceki_y + (hedef_y - onceki_y) / dinamik_yumusatma

                    pyautogui.moveTo(guncel_x, guncel_y)
                    onceki_x, onceki_y = guncel_x, guncel_y

                # DRAG AND DROP
                if acik_parmaklar[1:5] == [1, 0, 0, 0] or acik_parmaklar[1:5] == [0, 0, 0, 0]:
                    if mesafe_pinch < 40:
                        guncel_mod = "DRAGGING"
                        if not surukleniyor:
                            pyautogui.mouseDown()
                            surukleniyor = True
                            print("[ACTION] Mouse Down (Drag Started)")
                        cv2.circle(kare, (int((bas_x + isaret_x) / 2), int((bas_y + isaret_y) / 2)), 15, (0, 165, 255),
                                   cv2.FILLED)
                    else:
                        guncel_mod = "NAVIGATION"
                        if surukleniyor:
                            pyautogui.mouseUp()
                            surukleniyor = False
                            print("[ACTION] Mouse Up (Drag Ended)")

                        if acik_parmaklar[1:5] == [1, 0, 0, 0]:
                            cv2.drawMarker(kare, (isaret_x, isaret_y), (255, 0, 0), cv2.MARKER_CROSS, 15, 2)

                    kaydirma_onceki_y = 0

                # LEFT CLICK
                elif acik_parmaklar[1:5] == [1, 1, 0, 0]:
                    guncel_mod = "READY TO CLICK"
                    if surukleniyor: pyautogui.mouseUp(); surukleniyor = False

                    mesafe_orta = math.hypot(orta_x - isaret_x, orta_y - isaret_y)
                    cv2.line(kare, (isaret_x, isaret_y), (orta_x, orta_y), (255, 0, 255), 3)

                    if mesafe_orta < 30 and (guncel_zaman - son_tiklama_zamani > 0.3):
                        cv2.circle(kare, (isaret_x, isaret_y), 15, (0, 255, 0), cv2.FILLED)
                        pyautogui.click()
                        print("[ACTION] Left Click")
                        son_tiklama_zamani = guncel_zaman
                    kaydirma_onceki_y = 0

                # RIGHT CLICK
                elif acik_parmaklar[1:5] == [1, 0, 0, 1]:
                    guncel_mod = "RIGHT CLICK"
                    if surukleniyor: pyautogui.mouseUp(); surukleniyor = False

                    cv2.line(kare, (isaret_x, isaret_y), (serce_x, serce_y), (255, 255, 0), 2)

                    if (guncel_zaman - son_sag_tiklama_zamani > 1.0):
                        cv2.circle(kare, (isaret_x, isaret_y), 15, (255, 255, 0), cv2.FILLED)
                        cv2.circle(kare, (serce_x, serce_y), 15, (255, 255, 0), cv2.FILLED)
                        pyautogui.rightClick()
                        print("[ACTION] Right Click")
                        son_sag_tiklama_zamani = guncel_zaman
                    kaydirma_onceki_y = 0

                # SCROLL
                elif acik_parmaklar[1:5] == [1, 1, 1, 0]:
                    guncel_mod = "SCROLLING"
                    if surukleniyor: pyautogui.mouseUp(); surukleniyor = False

                    yuzuk_x, yuzuk_y = noktalar[16][0], noktalar[16][1]
                    cv2.circle(kare, (isaret_x, isaret_y), 8, (0, 255, 0), cv2.FILLED)
                    cv2.circle(kare, (orta_x, orta_y), 8, (0, 255, 0), cv2.FILLED)
                    cv2.circle(kare, (yuzuk_x, yuzuk_y), 8, (0, 255, 0), cv2.FILLED)

                    if kaydirma_onceki_y == 0:
                        kaydirma_onceki_y = isaret_y
                    else:
                        fark = kaydirma_onceki_y - isaret_y
                        if abs(fark) > 3:
                            pyautogui.scroll(fark * 4)
                            kaydirma_onceki_y = isaret_y

                else:
                    guncel_mod = "STANDBY"
                    if surukleniyor:
                        pyautogui.mouseUp()
                        surukleniyor = False
                    kaydirma_onceki_y = 0

                if guncel_mod != onceki_mod:
                    print(f"[INFO] Mode: {guncel_mod}")
                    onceki_mod = guncel_mod

            else:
                if not kilit_bolgesi_mi:
                    guncel_mod = "SYSTEM SLEEP"
                    if guncel_mod != onceki_mod:
                        print(f"[INFO] Mode: {guncel_mod}")
                        onceki_mod = guncel_mod

                cv2.rectangle(kare, (cerceve_boslugu, cerceve_boslugu), (640 - cerceve_boslugu, 480 - cerceve_boslugu),
                              (0, 0, 255), 2)
                cv2.putText(kare, "SYSTEM SLEEP", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

                # İşlemciyi (CPU) rahatlat
                time.sleep(0.05)

                # --- HUD (Heads-Up Display) Panel ---
        fps = 1 / (time.time() - gecmis_zaman)
        gecmis_zaman = time.time()

        overlay = kare.copy()
        cv2.rectangle(overlay, (400, 10), (630, 80), (0, 0, 0), cv2.FILLED)
        cv2.addWeighted(overlay, 0.4, kare, 0.6, 0, kare)

        cv2.putText(kare, f'FPS: {int(fps)}', (410, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(kare, f'Mode:', (410, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(kare, guncel_mod, (470, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.putText(kare, "Press 'Q' to Exit", (460, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("AI Hand Controller V1.0", kare)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[SYSTEM] Shutting down...")
            break

# 4. GÜVENLİK ÖNLEMİ: Ne olursa olsun kapanırken fareyi serbest bırak (Failsafe)
finally:
    if surukleniyor:
        pyautogui.mouseUp()
        print("[CRITICAL] Forced MouseUp executed on shutdown to prevent mouse stickiness.")
    kamera.release()
    cv2.destroyAllWindows()
    print("[SYSTEM] Exit complete.")