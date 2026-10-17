import serial
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


# =========================================================
# إعداد الأردوينو / Arduino Setup
# =========================================================

ARDUINO_PORT = "COM4"
BAUD_RATE = 9600

try:
    ser = serial.Serial(
        ARDUINO_PORT,
        BAUD_RATE,
        timeout=0.1
    )
    print(f"تم الاتصال بنجاح مع الأردوينو على المنفذ {ARDUINO_PORT} / Connected successfully")

except Exception as e:
    print(f"خطأ في الاتصال بالأردوينو: {e} / Arduino connection error")
    ser = None


# =========================================================
# معلومات المزرعة / Farm Data
# =========================================================

farm_data = {
    "location_ar": "فيفاء",
    "location_en": "Fifaa",

    "latitude": 17.25,
    "longitude": 43.10,

    "elevation": 1800,

    "environment_ar": "جبلية",
    "environment_en": "Mountainous",

    "crop_ar": "النعناع",
    "crop_en": "Mint"
}


# =========================================================
# بيانات الحساسات / Sensor Data
# =========================================================

sensor_data = {
    # معلومات النبتة بالعربي والإنجليزي
    "plant_name_ar": "نبتة النعناع",
    "plant_name_en": "Mint Plant",

    "plant_status_ar": "✓ بحالة ممتازة",
    "plant_status_en": "✓ Excellent Condition",

    "status_message_ar": "تم فحص حالة النبتة، وكل شيء يعمل بشكل صحيح.",
    "status_message_en": "Plant status checked, everything is functioning properly.",

    # التربة / Soil
    "soil_moisture": 45,
    "soil_salinity": 1.2,

    # الجو / Air
    "air_humidity": 55,
    "temperature": 26,

    # الخزان / Water Tank
    "water_level": 0,

    # معلومات الري / Watering Info
    "watering_count": 3,
    "last_watering": "10:30 AM",

    "watering_duration_ar": "45 ثانية",
    "watering_duration_en": "45 seconds",

    "watering_percentage": 90,
    "plant_need": 35
}


# =========================================================
# الخوارزمية الذكية (ثنائية اللغة) / Smart Algorithm
# =========================================================

def smart_irrigation(lang="ar"):
    soil_moisture = sensor_data["soil_moisture"]
    temperature = sensor_data["temperature"]
    crop = farm_data["crop_ar"]
    environment = farm_data["environment_ar"]
    elevation = farm_data["elevation"]

    # احتياج أساسي حسب المحصول
    crop_need = {
        "النعناع": 50,
        "نعناع": 50,
        "طماطم": 55,
        "مانجو": 45,
        "موز": 65,
        "بن": 40
    }

    base_need = crop_need.get(crop, 50)

    # تأثير رطوبة التربة
    if soil_moisture < 30:
        need = base_need + 25
    elif soil_moisture < 45:
        need = base_need + 10
    elif soil_moisture < 60:
        need = base_need
    else:
        need = base_need - 20

    # تأثير الحرارة
    if temperature >= 35:
        need += 20
    elif temperature >= 30:
        need += 10
    elif temperature <= 20:
        need -= 10

    # تأثير البيئة
    if environment == "جبلية":
        need -= 10
    elif environment == "ساحلية":
        need += 10

    # تأثير الارتفاع
    if elevation >= 1000:
        need -= 5

    # الضبط بين 0 و100
    need = max(0, min(100, need))

    # تحديد قرار وسبب الري بناءً على اللغة المطلوبة
    if lang == "en":
        if need >= 70:
            irrigation_status = "Needs Irrigation Now"
            irrigation_action = "🚿 Turn on Irrigation System"
        elif need >= 45:
            irrigation_status = "Needs Irrigation Soon"
            irrigation_action = "💧 Irrigation Recommended Soon"
        else:
            irrigation_status = "No Irrigation Needed"
            irrigation_action = "✓ Soil Moisture is Optimal"

        reason = (
            f"Recommendation based on farm location ({farm_data['location_en']}), "
            f"elevation ({elevation} m), environment ({farm_data['environment_en']}), "
            f"crop ({farm_data['crop_en']}), temperature ({temperature}°C), "
            f"and soil moisture ({soil_moisture}%)."
        )
    else:
        if need >= 70:
            irrigation_status = "يحتاج إلى الري الآن"
            irrigation_action = "🚿 تشغيل نظام الري"
        elif need >= 45:
            irrigation_status = "يحتاج إلى ري قريبًا"
            irrigation_action = "💧 يوصى بالري قريبًا"
        else:
            irrigation_status = "لا يحتاج إلى الري حاليًا"
            irrigation_action = "✓ التربة مناسبة"

        reason = (
            f"تم تحديد التوصية بناءً على موقع المزرعة ({farm_data['location_ar']})، "
            f"وارتفاعها ({elevation} متر)، ونوع البيئة ({farm_data['environment_ar']})، "
            f"ونوع المحصول ({farm_data['crop_ar']})، ودرجة الحرارة ({temperature}°C)، "
            f"ورطوبة التربة ({soil_moisture}%)."
        )

    return {
        "plant_need": need,
        "irrigation_status": irrigation_status,
        "irrigation_action": irrigation_action,
        "irrigation_reason": reason
    }


# =========================================================
# صفحات الموقع / Web Routes
# =========================================================

# الصفحة الرئيسية (عربي كافتراضي)
@app.route("/")
def index():
    return render_template("indexAr.html")


# الصفحة العربية
@app.route("/ar")
def index_ar():
    return render_template("indexAr.html")


# الصفحة الإنجليزية
@app.route("/en")
def index_en():
    return render_template("indexEn.html")


# =========================================================
# API البيانات / Data API
# =========================================================

@app.route("/data")
def get_data():
    lang = request.args.get("lang", "ar")

    # قراءة مستوى الماء الحقيقي من Arduino
    if ser and ser.is_open:
        try:
            while ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="ignore").strip()

                if line.isdigit():
                    water_value = int(line)
                    water_value = max(0, min(100, water_value))
                    sensor_data["water_level"] = water_value

        except Exception as e:
            print(f"خطأ أثناء قراءة الأردوينو: {e}")

    # تشغيل الخوارزمية للغة المحددة
    irrigation = smart_irrigation(lang=lang)

    # تجهيز الاستجابة بحسب اللغة
    if lang == "en":
        response_data = {
            **sensor_data,
            "plant_name": sensor_data["plant_name_en"],
            "plant_status": sensor_data["plant_status_en"],
            "status_message": sensor_data["status_message_en"],
            "watering_duration": sensor_data["watering_duration_en"],
            "location": farm_data["location_en"],
            "environment": farm_data["environment_en"],
            "crop": farm_data["crop_en"],
            "elevation": farm_data["elevation"],
            "latitude": farm_data["latitude"],
            "longitude": farm_data["longitude"],
            **irrigation
        }
    else:
        response_data = {
            **sensor_data,
            "plant_name": sensor_data["plant_name_ar"],
            "plant_status": sensor_data["plant_status_ar"],
            "status_message": sensor_data["status_message_ar"],
            "watering_duration": sensor_data["watering_duration_ar"],
            "location": farm_data["location_ar"],
            "environment": farm_data["environment_ar"],
            "crop": farm_data["crop_ar"],
            "elevation": farm_data["elevation"],
            "latitude": farm_data["latitude"],
            "longitude": farm_data["longitude"],
            **irrigation
        }

    return jsonify(response_data)


# =========================================================
# تشغيل السيرفر / Run Server
# =========================================================

if __name__ == "__main__":
    print("\n======================================")
    print("🌱 Smart Irrigation System")
    print("======================================")
    print("🌐 رابط اللغة العربية:  http://127.0.0.1:5000/ar")
    print("🌐 English Link:         http://127.0.0.1:5000/en")
    print("======================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
