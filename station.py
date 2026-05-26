import logging
from bahn_gui import BahnGui
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bahn_monitor.log"),
        logging.StreamHandler(),
    ],
)

if __name__ == "__main__":
    app = BahnGui(settings)
    app.after(settings.update_interval, app.start_auto_update)
    app.mainloop()
