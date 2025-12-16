"""Tests simplificados para services/audio_manager.py"""
import pytest
from unittest.mock import Mock, patch
from services.audio_manager import AudioManager


class TestAudioManagerBasics:
    """Tests básicos del gestor de audio."""
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_initialization(self, mock_sound, mock_channel):
        """Verificar inicialización básica."""
        manager = AudioManager()
        assert manager is not None
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_music_channel(self, mock_sound, mock_channel):
        """Verificar que tiene canal de música."""
        manager = AudioManager()
        assert hasattr(manager, 'music_channel')
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_music_volume_default(self, mock_sound, mock_channel):
        """Verificar volumen de música por defecto."""
        manager = AudioManager()
        assert manager.music_volume == 0.5
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_play_music_method(self, mock_sound, mock_channel):
        """Verificar que tiene método play_music."""
        manager = AudioManager()
        assert hasattr(manager, 'play_music')
        assert callable(manager.play_music)
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_stop_music_method(self, mock_sound, mock_channel):
        """Verificar que tiene método stop_music."""
        manager = AudioManager()
        assert hasattr(manager, 'stop_music')
        assert callable(manager.stop_music)
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_play_footstep_method(self, mock_sound, mock_channel):
        """Verificar que tiene método play_footstep."""
        manager = AudioManager()
        assert hasattr(manager, 'play_footstep')
        assert callable(manager.play_footstep)
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_play_blood_sound_method(self, mock_sound, mock_channel):
        """Verificar que tiene método play_blood_sound."""
        manager = AudioManager()
        assert hasattr(manager, 'play_blood_sound')
        assert callable(manager.play_blood_sound)
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_subtitle_system_initialized(self, mock_sound, mock_channel):
        """Verificar que el sistema de subtítulos está inicializado."""
        manager = AudioManager()
        assert hasattr(manager, 'showing_subtitles')
        assert manager.showing_subtitles == False
        assert hasattr(manager, 'subtitle_text')
        assert manager.subtitle_text == ""
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_thought_system_initialized(self, mock_sound, mock_channel):
        """Verificar que el sistema de pensamientos está inicializado."""
        manager = AudioManager()
        assert hasattr(manager, 'thought_active')
        assert manager.thought_active == False
        assert hasattr(manager, 'thought_blocks_movement')
        assert manager.thought_blocks_movement == False
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_fade_system_initialized(self, mock_sound, mock_channel):
        """Verificar que el sistema de fade está inicializado."""
        manager = AudioManager()
        assert hasattr(manager, 'fading_out')
        assert manager.fading_out == False
        assert hasattr(manager, 'fading_in')
        assert manager.fading_in == False
        assert hasattr(manager, 'fade_duration')
        assert manager.fade_duration == 1000
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_music_sounds_dict(self, mock_sound, mock_channel):
        """Verificar que tiene diccionario de sonidos musicales."""
        manager = AudioManager()
        assert hasattr(manager, 'music_sounds')
        assert isinstance(manager.music_sounds, dict)
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_has_update_method(self, mock_sound, mock_channel):
        """Verificar que tiene método update."""
        manager = AudioManager()
        assert hasattr(manager, 'update')
        assert callable(manager.update)
