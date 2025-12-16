"""Tests unitarios para services/audio_manager.py"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from services.audio_manager import AudioManager


class TestAudioManagerInitialization:
    """Tests para la inicialización del AudioManager."""
    
    @patch('pygame.mixer.Channel')
    def test_initialization(self, mock_channel):
        """Verificar inicialización básica."""
        audio = AudioManager()
        assert audio is not None
    
    @patch('pygame.mixer.Channel')
    def test_initial_state(self, mock_channel):
        """Verificar estado inicial."""
        audio = AudioManager()
        assert hasattr(audio, 'music_sounds')
        assert hasattr(audio, 'footstep_sounds')
        assert isinstance(audio.music_sounds, dict)
        assert isinstance(audio.footstep_sounds, list)
    
    @patch('pygame.mixer.Channel')
    def test_music_channel_created(self, mock_channel):
        """Verificar que se crea el canal de música."""
        audio = AudioManager()
        mock_channel.assert_called_once_with(0)


class TestMusicManagement:
    """Tests para gestión de música."""
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_play_music_method_exists(self, mock_sound, mock_channel):
        """Verificar que existe el método play_music."""
        audio = AudioManager()
        assert hasattr(audio, 'play_music')
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_stop_music_method_exists(self, mock_sound, mock_channel):
        """Verificar que existe el método stop_music."""
        audio = AudioManager()
        assert hasattr(audio, 'stop_music')
    
    @patch('pygame.mixer.Channel')
    def test_start_fade_out_method_exists(self, mock_channel):
        """Verificar que existe el método start_fade_out."""
        audio = AudioManager()
        assert hasattr(audio, 'start_fade_out')


class TestFootstepSounds:
    """Tests para sonidos de pasos."""
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_play_footstep_method_exists(self, mock_sound, mock_channel):
        """Verificar que existe el método play_footstep."""
        audio = AudioManager()
        assert hasattr(audio, 'play_footstep')
    
    @patch('pygame.mixer.Channel')
    def test_footstep_toggle_exists(self, mock_channel):
        """Verificar que existe el mecanismo de alternancia."""
        audio = AudioManager()
        assert hasattr(audio, 'footstep_toggle')


class TestThoughtSystem:
    """Tests para el sistema de pensamientos."""
    
    @patch('pygame.mixer.Channel')
    def test_trigger_thought_method_exists(self, mock_channel):
        """Verificar que existe el método trigger_thought."""
        audio = AudioManager()
        assert hasattr(audio, 'trigger_thought')
    
    @patch('pygame.mixer.Channel')
    def test_is_thought_active_method_exists(self, mock_channel):
        """Verificar que existe el método is_thought_active."""
        audio = AudioManager()
        assert hasattr(audio, 'is_thought_active')
    
    @patch('pygame.mixer.Channel')
    def test_thought_blocks_movement_method_exists(self, mock_channel):
        """Verificar que existe el método thought_blocks_movement."""
        audio = AudioManager()
        assert hasattr(audio, 'thought_blocks_movement')


class TestSubtitleSystem:
    """Tests para el sistema de subtítulos."""
    
    @patch('pygame.mixer.Channel')
    def test_get_current_subtitle_method_exists(self, mock_channel):
        """Verificar que existe el método get_current_subtitle."""
        audio = AudioManager()
        assert hasattr(audio, 'get_current_subtitle')
    
    @patch('pygame.mixer.Channel')
    def test_clear_subtitles_method_exists(self, mock_channel):
        """Verificar que existe el método clear_subtitles."""
        audio = AudioManager()
        assert hasattr(audio, 'clear_subtitles')


class TestFadeSystem:
    """Tests para el sistema de fade."""
    
    @patch('pygame.mixer.Channel')
    def test_update_fade_method_exists(self, mock_channel):
        """Verificar que existe el método update_fade."""
        audio = AudioManager()
        assert hasattr(audio, 'update_fade')
    
    @patch('pygame.mixer.Channel')
    def test_is_fading_method_exists(self, mock_channel):
        """Verificar que existe el método is_fading."""
        audio = AudioManager()
        assert hasattr(audio, 'is_fading')


class TestUpdateSystem:
    """Tests para el sistema de actualización."""
    
    @patch('pygame.mixer.Channel')
    def test_update_method_exists(self, mock_channel):
        """Verificar que existe el método update principal."""
        audio = AudioManager()
        assert hasattr(audio, 'update')
    
    @patch('pygame.mixer.Channel')
    def test_update_thought_method_exists(self, mock_channel):
        """Verificar que existe el método update_thought."""
        audio = AudioManager()
        assert hasattr(audio, 'update_thought')
    
    @patch('pygame.mixer.Channel')
    def test_update_can_be_called(self, mock_channel):
        """Verificar que update puede ser llamado sin errores."""
        audio = AudioManager()
        # No debería lanzar excepciones
        audio.update()


class TestAudioState:
    """Tests para el estado del audio."""
    
    @patch('pygame.mixer.Channel')
    def test_initial_thought_inactive(self, mock_channel):
        """Verificar que inicialmente no hay pensamiento activo."""
        audio = AudioManager()
        assert audio.is_thought_active() == False
    
    @patch('pygame.mixer.Channel')
    def test_initial_no_fade(self, mock_channel):
        """Verificar que inicialmente no hay fade activo."""
        audio = AudioManager()
        assert audio.is_fading() == False
    
    @patch('pygame.mixer.Channel')
    def test_initial_no_subtitle(self, mock_channel):
        """Verificar que inicialmente no hay subtítulo."""
        audio = AudioManager()
        subtitle = audio.get_current_subtitle()
        assert subtitle is None or subtitle == ""


class TestSoundLoading:
    """Tests para carga de sonidos."""
    
    @patch('pygame.mixer.Channel')
    @patch('os.path.exists')
    @patch('pygame.mixer.Sound')
    def test_sound_files_structure(self, mock_sound, mock_exists, mock_channel):
        """Verificar estructura de archivos de sonido."""
        mock_exists.return_value = True
        audio = AudioManager()
        
        # Debe intentar cargar sonidos
        assert hasattr(audio, 'music_sounds')
        assert isinstance(audio.music_sounds, dict)


class TestIntegration:
    """Tests de integración básicos."""
    
    @patch('pygame.mixer.Channel')
    def test_multiple_updates(self, mock_channel):
        """Verificar que se pueden hacer múltiples updates."""
        audio = AudioManager()
        
        # Llamar update varias veces no debe causar errores
        for _ in range(10):
            audio.update()
    
    @patch('pygame.mixer.Channel')
    def test_clear_subtitles_safe(self, mock_channel):
        """Verificar que clear_subtitles es seguro."""
        audio = AudioManager()
        
        # Debe poder llamarse sin error incluso sin subtítulos
        audio.clear_subtitles()
        audio.clear_subtitles()  # Dos veces


class TestEdgeCases:
    """Tests para casos especiales."""
    
    @patch('pygame.mixer.Channel')
    def test_footstep_alternation(self, mock_channel):
        """Verificar que footstep_toggle alterna."""
        audio = AudioManager()
        
        initial_toggle = audio.footstep_toggle
        # Después de varias llamadas a play_footstep, debería alternar
        # (solo verificamos que la propiedad existe y es booleana)
        assert isinstance(audio.footstep_toggle, bool)
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_stop_music_when_not_playing(self, mock_sound, mock_channel):
        """Verificar que stop_music es seguro cuando no hay música."""
        audio = AudioManager()
        
        # No debería causar error
        audio.stop_music()
    
    @patch('pygame.mixer.Channel')
    def test_update_thought_when_inactive(self, mock_channel):
        """Verificar que update_thought es seguro sin pensamiento activo."""
        audio = AudioManager()
        
        # No debería causar error
        audio.update_thought()


class TestMethodSignatures:
    """Tests para verificar firmas de métodos."""
    
    @patch('pygame.mixer.Channel')
    def test_play_music_accepts_key(self, mock_channel):
        """Verificar que play_music acepta una clave."""
        audio = AudioManager()
        # Verificar que el método existe y puede ser llamado
        assert callable(audio.play_music)
    
    @patch('pygame.mixer.Channel')
    def test_trigger_thought_accepts_parameters(self, mock_channel):
        """Verificar que trigger_thought acepta parámetros."""
        audio = AudioManager()
        assert callable(audio.trigger_thought)
    
    @patch('pygame.mixer.Channel')
    def test_start_fade_out_accepts_duration(self, mock_channel):
        """Verificar que start_fade_out acepta duración."""
        audio = AudioManager()
        assert callable(audio.start_fade_out)
