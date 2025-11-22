# -*- coding: utf-8 -*-
"""
Менеджер текст-в-мова (TTS) функціоналу з використанням Android TTS.
"""
from kivy.logger import Logger

try:
    from jnius import autoclass
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')
    HashMap = autoclass('java.util.HashMap')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    ANDROID_TTS_AVAILABLE = True
except ImportError:
    ANDROID_TTS_AVAILABLE = False
    Logger.warning("TTS: pyjnius не доступний, TTS не працюватиме")


class TTSManager:
    """Керування TTS функціоналом з використанням Android TTS."""

#-------------------------------------------    
    def __init__(self):
        self.is_speaking = False
        self.tts_engine = None
        
        if ANDROID_TTS_AVAILABLE:
            self._init_android_tts()

#-------------------------------------------    
    def _init_android_tts(self):
        """Ініціалізація Android TTS."""
        try:
            self.tts_engine = TextToSpeech(PythonActivity.mActivity, None)
            # Спроба встановити українську мову
            try:
                self.tts_engine.setLanguage(Locale.forLanguageTag("uk-UA"))
            except Exception:
                try:
                    self.tts_engine.setLanguage(Locale("uk"))
                except Exception:
                    pass
            Logger.info("\n_init_android_tts: TTS: Android TTS ініціалізовано\n")
        except Exception as e:
            Logger.error(f"\n_init_android_tts: TTS: Помилка ініціалізації Android TTS: {e}\n")

#-------------------------------------------    
    def safe_tts_speak(self, text: str):
        """Безпечне відтворення тексту через TTS."""
        try:
            if not ANDROID_TTS_AVAILABLE or not self.tts_engine:
                Logger.error("\nsafe_tts_speak: TTS: Двигун не доступний\n")
                return
                
            text = text.strip()
            if not text:
                Logger.warning("\nsafe_tts_speak: TTS: Спроба відтворення порожнього тексту")
                return
            
            # Зупиняємо попереднє відтворення
            self.stop_tts()
            
            # Встановлюємо параметри (гучність)
            params = HashMap()
            params.put("volume", "1.0")
            
            # Відтворюємо текст
            self.tts_engine.speak(text, TextToSpeech.QUEUE_FLUSH, params)
            self.is_speaking = True
            
            Logger.info(f"\nsafe_tts_speak: TTS: Відтворення тексту ({len(text)} символів)\n")
            Logger.debug(f"\nsafe_tts_speak: TTS: Текст для відтворення: '{text[:50]}{'...' if len(text) > 50 else ''}'\n")
            
        except Exception as e:
            Logger.error(f"\nsafe_tts_speak: TTS помилка: {e}\n")
            self.is_speaking = False
 
 #-------------------------------------------   
    def stop_tts(self):
        """Зупиняє TTS відтворення."""
        try:
            if self.is_speaking and ANDROID_TTS_AVAILABLE and self.tts_engine:
                self.tts_engine.stop()
                Logger.info("\nstop_tts: TTS: Відтворення зупинено\n")
            self.is_speaking = False
        except Exception as e:
            Logger.error(f"\nstop_tts:TTS помилка зупинки: {e}\n")

#-------------------------------------------    
    def is_playing(self) -> bool:
        """Перевіряє, чи відтворюється звук."""
        return self.is_speaking

#-------------------------------------------        
    def set_speech_rate(self, rate: float):
        """Встановлює швидкість мовлення (0.5 - 2.0)."""
        try:
            if ANDROID_TTS_AVAILABLE and self.tts_engine:
                self.tts_engine.setSpeechRate(rate)
                Logger.info(f"\nset_speech_rate: TTS: Швидкість встановлено на {rate}\n")
        except Exception as e:
            Logger.error(f"\nset_speech_rate: TTS: Помилка встановлення швидкості: {e}\n")

#-------------------------------------------    
    def set_pitch(self, pitch: float):
        """Встановлює висоту тону (0.5 - 2.0)."""
        try:
            if ANDROID_TTS_AVAILABLE and self.tts_engine:
                self.tts_engine.setPitch(pitch)
                Logger.info(f"\nset_pitch: TTS: Висота тону встановлена на {pitch}\n")
        except Exception as e:
            Logger.error(f"\nset_pitch: TTS: Помилка встановлення висоти тону: {e}\n")

#-------------------------------------------        
    def shutdown(self):
        """Завершує роботу TTS."""
        try:
            if ANDROID_TTS_AVAILABLE and self.tts_engine:
                self.tts_engine.shutdown()
                Logger.info("\nshutdown: TTS: Двигун вимкнено\n")
        except Exception as e:
            Logger.error(f"\nshutdown: TTS: Помилка вимкнення: {e}\n")
 #-------------------------------------------           
 
# gTTS
#try:
#    from gtts import gTTS
#except:
#    gTTS = None

#try:
#    from pydub import AudioSegment
#except:
#    AudioSegment = None
#    
# def tts_generate_gtts(text: str, out_path: Path, lang: str='uk') -> bool:
#    if gTTS is None:
#        logging.error("\ngTTS не встановлено")
#        return False
#    try:
#        gTTS(text=text, lang=lang).save(str(out_path))
#        return True
#    except Exception as e:
#        logging.exception(f"\ngTTS помилка: {e}")
#        return False

 #-------------------------------------------    
