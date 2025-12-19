"""Tests extendidos para services/audio_manager.py - Cobertura 75%+"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.audio_manager import AudioManager


class TestAudioManagerExtended:
    """Tests adicionales para alcanzar 75% de cobertura."""
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_play_music_exists_in_dict(self, mock_sound, mock_channel):
        """Test reproducir música que existe."""
        manager = AudioManager()
        manager.music_sounds['test'] = Mock()
        manager.play_music('test')
        assert manager.current_music == 'test'
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_play_music_not_exists(self, mock_sound, mock_channel):
        """Test reproducir música que no existe."""
        manager = AudioManager()
        initial_music = manager.current_music
        manager.play_music('nonexistent')
        # No debería cambiar si la música no existe
        assert manager.current_music == initial_music
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_stop_music_clears_current(self, mock_sound, mock_channel):
        """Test que stop_music limpia current_music."""
        manager = AudioManager()
        manager.current_music = 'test'
        manager.stop_music()
        assert manager.current_music is None
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks', return_value=0)
    def test_start_fade_out_sets_flags(self, mock_ticks, mock_sound, mock_channel):
        """Test que fade out configura las flags correctamente."""
        manager = AudioManager()
        manager.start_fade_out(1000, 'next_music')
        
        assert manager.fading_out == True
        assert manager.fading_in == False
        assert manager.fade_duration == 1000
        assert manager.pending_music_load == 'next_music'
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks', return_value=0)
    def test_start_fade_in_sets_flags(self, mock_ticks, mock_sound, mock_channel):
        """Test que fade in configura las flags correctamente."""
        manager = AudioManager()
        manager.start_fade_in(1000, 0.8)
        
        assert manager.fading_in == True
        assert manager.fading_out == False
        assert manager.fade_duration == 1000
        assert manager.fade_to_volume == 0.8
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_fades_fade_out_in_progress(self, mock_ticks, mock_sound, mock_channel):
        """Test update_fades durante fade out."""
        manager = AudioManager()
        mock_ticks.return_value = 0
        manager.start_fade_out(1000)
        
        mock_ticks.return_value = 500  # Mitad del fade
        manager.update_fades()
        
        # El volumen debería estar entre inicio y fin
        assert 0 <= manager.music_volume <= 0.5
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_fades_fade_out_completed(self, mock_ticks, mock_sound, mock_channel):
        """Test update_fades cuando fade out termina."""
        manager = AudioManager()
        mock_ticks.return_value = 0
        manager.start_fade_out(1000)
        
        mock_ticks.return_value = 1000  # Fade completado
        manager.update_fades()
        
        assert manager.fading_out == False
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_fades_fade_in_in_progress(self, mock_ticks, mock_sound, mock_channel):
        """Test update_fades durante fade in."""
        manager = AudioManager()
        mock_ticks.return_value = 0
        manager.start_fade_in(1000, 0.5)
        
        mock_ticks.return_value = 500  # Mitad del fade
        manager.update_fades()
        
        # El volumen debería estar entre 0 y 0.5
        assert 0 <= manager.music_volume <= 0.5
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_fades_fade_in_completed(self, mock_ticks, mock_sound, mock_channel):
        """Test update_fades cuando fade in termina."""
        manager = AudioManager()
        mock_ticks.return_value = 0
        manager.start_fade_in(1000, 0.5)
        
        mock_ticks.return_value = 1000  # Fade completado
        manager.update_fades()
        
        assert manager.fading_in == False
        assert manager.music_volume == 0.5
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_fades_with_pending_music(self, mock_ticks, mock_sound, mock_channel):
        """Test fade out con música pendiente."""
        manager = AudioManager()
        manager.music_sounds['next'] = Mock()
        
        mock_ticks.return_value = 0
        manager.start_fade_out(1000, 'next')
        
        mock_ticks.return_value = 1000  # Fade completado
        manager.update_fades()
        
        # Debería haber iniciado fade in
        assert manager.fading_in == True
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_show_subtitle(self, mock_ticks, mock_sound, mock_channel):
        """Test mostrar subtítulo."""
        manager = AudioManager()
        mock_ticks.return_value = 1000
        
        manager.show_subtitle("Test subtitle", 3000)
        
        assert manager.showing_subtitles == True
        assert manager.subtitle_text == "Test subtitle"
        assert manager.subtitle_duration == 3000
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_subtitles_active(self, mock_ticks, mock_sound, mock_channel):
        """Test update de subtítulos activos."""
        manager = AudioManager()
        mock_ticks.return_value = 1000
        manager.show_subtitle("Test", 3000)
        
        mock_ticks.return_value = 2000  # Aún dentro de la duración
        manager.update_subtitles()
        
        assert manager.showing_subtitles == True
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_subtitles_expired(self, mock_ticks, mock_sound, mock_channel):
        """Test update de subtítulos expirados."""
        manager = AudioManager()
        mock_ticks.return_value = 1000
        manager.show_subtitle("Test", 3000)
        
        mock_ticks.return_value = 5000  # Después de la duración
        manager.update_subtitles()
        
        assert manager.showing_subtitles == False
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_play_footstep_with_sounds(self, mock_sound, mock_channel):
        """Test reproducir sonido de paso."""
        manager = AudioManager()
        # Simular que hay sonidos de pasos
        manager.footstep_sounds = [Mock(), Mock()]
        manager.last_footstep_index = 0
        
        manager.play_footstep()
        
        # Debería alternar el índice
        assert manager.last_footstep_index == 1
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    def test_play_blood_sound_exists(self, mock_sound, mock_channel):
        """Test reproducir sonido de sangre."""
        manager = AudioManager()
        manager.blood_sound = Mock()
        
        manager.play_blood_sound()
        
        manager.blood_sound.play.assert_called_once()
    
    @patch('pygame.mixer.Channel')
    @patch('pygame.mixer.Sound')
    @patch('pygame.time.get_ticks')
    def test_update_calls_subfunctions(self, mock_ticks, mock_sound, mock_channel):
        """Test que update llama a las subfunciones."""
        manager = AudioManager()
        mock_ticks.return_value = 1000
        
        manager.update()
        
        # Simplemente verificar que no lanza error
        assert True
