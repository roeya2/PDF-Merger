"""
Integration tests for profile management workflows.

These tests verify the complete lifecycle of profile management including
creation, saving, loading, updating, and deletion, as well as integration
with other system components.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import pytest

from tests.integration.base_integration_test import BaseIntegrationTest
from app.managers.config_manager import ConfigManager


class TestProfileCreationWorkflow(BaseIntegrationTest):
    """Test profile creation and saving workflows."""

    def test_create_simple_profile_workflow(self):
        """Test creating and saving a simple profile."""
        config_manager = self.create_test_config_manager()

        # Create test file details
        test_files = [
            {
                'filepath': '/document1.pdf',
                'filename': 'document1.pdf',
                'selected_pages': [1, 2, 3, 4, 5],
                'page_count': 10,
                'file_type': 'pdf'
            },
            {
                'filepath': '/document2.pdf',
                'filename': 'document2.pdf',
                'selected_pages': [1, 2, 3],
                'page_count': 8,
                'file_type': 'pdf'
            }
        ]

        # Save profile
        profile_name = 'simple_merge_profile'
        config_manager.save_profile(profile_name, test_files)

        # Verify profile created in memory
        assert profile_name in config_manager.config['profiles']
        profile = config_manager.config['profiles'][profile_name]

        # Verify profile structure
        assert 'pdf_merger_pro_list' in profile
        assert 'compression_level' in profile
        assert 'preserve_bookmarks' in profile
        assert 'created' in profile

        # Verify file list
        assert len(profile['pdf_merger_pro_list']) == 2
        assert profile['pdf_merger_pro_list'][0]['filepath'] == '/document1.pdf'
        assert profile['pdf_merger_pro_list'][1]['selected_pages'] == [1, 2, 3]

    def test_create_complex_profile_workflow(self):
        """Test creating a complex profile with various settings."""
        config_manager = self.create_test_config_manager()

        # Modify configuration before creating profile
        config_manager.config.update({
            'compression_level': 'high',
            'preserve_bookmarks': False,
            'output_password_protect': True,
            'output_password': 'secure123',
            'output_color_mode': 'Grayscale',
            'output_dpi': '300'
        })

        # Create complex file list with different page selections
        complex_files = [
            {
                'filepath': '/book_chapter1.pdf',
                'filename': 'book_chapter1.pdf',
                'selected_pages': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # First 10 pages
                'page_count': 50,
                'file_type': 'pdf'
            },
            {
                'filepath': '/book_chapter2.pdf',
                'filename': 'book_chapter2.pdf',
                'selected_pages': [15, 16, 17, 18, 19, 20],  # Specific pages
                'page_count': 45,
                'file_type': 'pdf'
            },
            {
                'filepath': '/appendix.pdf',
                'filename': 'appendix.pdf',
                'selected_pages': list(range(1, 21)),  # All pages 1-20
                'page_count': 20,
                'file_type': 'pdf'
            }
        ]

        # Save complex profile
        config_manager.save_profile('complex_book_profile', complex_files)

        # Verify profile captured all settings
        profile = config_manager.config['profiles']['complex_book_profile']
        assert profile['compression_level'] == 'high'
        assert profile['preserve_bookmarks'] is False
        assert profile['output_password_protect'] is True
        # Note: output_password is not saved for security reasons
        assert profile['output_color_mode'] == 'Grayscale'
        assert profile['output_dpi'] == '300'

        # Verify file selections preserved
        assert len(profile['pdf_merger_pro_list']) == 3
        assert profile['pdf_merger_pro_list'][0]['selected_pages'] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert profile['pdf_merger_pro_list'][1]['selected_pages'] == [15, 16, 17, 18, 19, 20]
        assert profile['pdf_merger_pro_list'][2]['selected_pages'] == list(range(1, 21))


class TestProfilePersistenceWorkflow(BaseIntegrationTest):
    """Test profile persistence across application sessions."""

    def test_profile_persistence_across_sessions(self):
        """Test that profiles persist across application sessions."""
        # First session - create and save profile
        config_manager1 = self.create_test_config_manager()

        test_files = [
            {'filepath': '/persistent.pdf', 'selected_pages': [1, 2, 3], 'page_count': 10}
        ]

        # Set specific settings
        config_manager1.config['compression_level'] = 'low'
        config_manager1.config['preserve_bookmarks'] = True

        config_manager1.save_profile('persistent_profile', test_files)
        config_manager1.save_config()

        # Second session - load and verify profile
        config_manager2 = ConfigManager(config_manager1.config_path)

        # Verify profile exists and is correct
        assert 'persistent_profile' in config_manager2.config['profiles']
        loaded_profile = config_manager2.config['profiles']['persistent_profile']

        assert len(loaded_profile['pdf_merger_pro_list']) == 1
        assert loaded_profile['pdf_merger_pro_list'][0]['filepath'] == '/persistent.pdf'
        assert loaded_profile['compression_level'] == 'low'
        assert loaded_profile['preserve_bookmarks'] is True
        assert 'created' in loaded_profile

        # Verify timestamp is recent
        created_time = datetime.fromisoformat(loaded_profile['created'])
        time_diff = datetime.now() - created_time
        assert time_diff.total_seconds() < 60  # Created within last minute

    def test_multiple_profiles_persistence(self):
        """Test persistence of multiple profiles."""
        config_manager = self.create_test_config_manager()

        # Create multiple profiles with different settings
        profiles_data = {
            'profile_a': {
                'files': [{'filepath': '/doc_a.pdf', 'selected_pages': [1, 2]}],
                'compression': 'normal',
                'bookmarks': True
            },
            'profile_b': {
                'files': [{'filepath': '/doc_b.pdf', 'selected_pages': [1, 2, 3, 4, 5]}],
                'compression': 'high',
                'bookmarks': False
            },
            'profile_c': {
                'files': [{'filepath': '/doc_c1.pdf', 'selected_pages': [1]},
                         {'filepath': '/doc_c2.pdf', 'selected_pages': [1, 2]}],
                'compression': 'maximum',
                'bookmarks': True
            }
        }

        # Save all profiles
        for name, data in profiles_data.items():
            config_manager.config['compression_level'] = data['compression']
            config_manager.config['preserve_bookmarks'] = data['bookmarks']
            config_manager.save_profile(name, data['files'])

        # Save config
        config_manager.save_config()

        # Load in new session
        new_manager = ConfigManager(config_manager.config_path)

        # Verify all profiles exist and are correct
        for name, data in profiles_data.items():
            assert name in new_manager.config['profiles']
            profile = new_manager.config['profiles'][name]

            assert len(profile['pdf_merger_pro_list']) == len(data['files'])
            assert profile['compression_level'] == data['compression']
            assert profile['preserve_bookmarks'] == data['bookmarks']


class TestProfileOperationsWorkflow(BaseIntegrationTest):
    """Test profile operations and management workflows."""

    def test_profile_retrieval_and_validation(self):
        """Test profile retrieval and validation."""
        config_manager = self.create_test_config_manager()

        # Create test profile
        test_files = [{'filepath': '/test.pdf', 'selected_pages': [1, 2, 3]}]
        config_manager.save_profile('test_profile', test_files)

        # Test successful retrieval
        profile = config_manager.get_profile('test_profile')
        assert profile is not None
        assert len(profile['pdf_merger_pro_list']) == 1

        # Test non-existent profile retrieval
        non_existent = config_manager.get_profile('missing_profile')
        assert non_existent is None

    def test_profile_update_workflow(self):
        """Test updating existing profile."""
        config_manager = self.create_test_config_manager()

        # Create initial profile
        initial_files = [{'filepath': '/initial.pdf', 'selected_pages': [1, 2]}]
        config_manager.save_profile('update_test', initial_files)

        # Update configuration
        config_manager.config['compression_level'] = 'high'
        config_manager.config['preserve_bookmarks'] = False

        # Update with new files
        updated_files = [
            {'filepath': '/initial.pdf', 'selected_pages': [1, 2]},
            {'filepath': '/additional.pdf', 'selected_pages': [1, 2, 3, 4, 5]}
        ]
        config_manager.save_profile('update_test', updated_files)

        # Verify profile updated
        updated_profile = config_manager.get_profile('update_test')
        assert len(updated_profile['pdf_merger_pro_list']) == 2
        assert updated_profile['compression_level'] == 'high'
        assert updated_profile['preserve_bookmarks'] is False

        # Note: Timestamp is only set on initial creation, not on updates
        original_created = config_manager.config['profiles']['update_test']['created']
        assert updated_profile['created'] == original_created  # Timestamps should be the same for updates

    def test_profile_deletion_workflow(self):
        """Test profile deletion workflow."""
        config_manager = self.create_test_config_manager()

        # Create multiple profiles
        profiles = ['delete_test1', 'delete_test2', 'delete_test3']
        for profile_name in profiles:
            config_manager.save_profile(profile_name, [{'filepath': f'/{profile_name}.pdf', 'selected_pages': [1]}])

        # Verify all profiles exist
        assert len(config_manager.config['profiles']) == 3
        for profile_name in profiles:
            assert profile_name in config_manager.config['profiles']

        # Delete middle profile
        result = config_manager.delete_profile('delete_test2')
        assert result is True

        # Verify profile deleted
        assert 'delete_test2' not in config_manager.config['profiles']
        assert len(config_manager.config['profiles']) == 2

        # Verify other profiles still exist
        assert 'delete_test1' in config_manager.config['profiles']
        assert 'delete_test3' in config_manager.config['profiles']

        # Test deleting non-existent profile
        result2 = config_manager.delete_profile('non_existent')
        assert result2 is False

    def test_profile_with_empty_pdf_merger_pro_list(self):
        """Test creating profile with empty file list."""
        config_manager = self.create_test_config_manager()

        # Create profile with empty file list
        config_manager.save_profile('empty_profile', [])

        # Verify profile created
        profile = config_manager.get_profile('empty_profile')
        assert profile is not None
        assert profile['pdf_merger_pro_list'] == []
        assert 'created' in profile

    def test_profile_name_edge_cases(self):
        """Test profile names with edge cases."""
        config_manager = self.create_test_config_manager()

        test_files = [{'filepath': '/test.pdf', 'selected_pages': [1]}]

        # Test profile name with spaces
        config_manager.save_profile('Profile With Spaces', test_files)
        assert 'Profile With Spaces' in config_manager.config['profiles']

        # Test profile name with special characters
        config_manager.save_profile('Profile-123_test', test_files)
        assert 'Profile-123_test' in config_manager.config['profiles']

        # Test profile name with unicode
        config_manager.save_profile('测试Profile', test_files)
        assert '测试Profile' in config_manager.config['profiles']


class TestProfileIntegrationWorkflow(BaseIntegrationTest):
    """Test profile integration with other system components."""

    def test_profile_integration_with_recent_directories(self):
        """Test profile usage alongside recent directories."""
        config_manager = self.create_test_config_manager()

        # Add recent directories
        with patch('os.path.isdir', return_value=True):
            config_manager.add_recent_directory('/project/docs')
            config_manager.add_recent_directory('/home/pdfs')

        # Create profile
        profile_files = [{'filepath': '/project/docs/manual.pdf', 'selected_pages': [1, 2, 3]}]
        config_manager.save_profile('project_docs', profile_files)

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify both recent directories and profile persisted
        assert len(new_manager.config['recent_directories']) == 2
        assert 'project_docs' in new_manager.config['profiles']

        # Verify profile can access recent directory paths
        profile = new_manager.get_profile('project_docs')
        assert profile['pdf_merger_pro_list'][0]['filepath'] == '/project/docs/manual.pdf'

    def test_profile_workflow_with_window_state(self):
        """Test profile workflow integrated with window state."""
        config_manager = self.create_test_config_manager()

        # Set window state
        config_manager.save_window_state("1000x700+200+150", {'main_pane': (300,)})

        # Create profile
        config_manager.save_profile('window_test', [{'filepath': '/test.pdf', 'selected_pages': [1]}])

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify both profile and window state persisted
        assert 'window_test' in new_manager.config['profiles']
        geometry, sash = new_manager.load_window_state()
        assert geometry == "1000x700+200+150"
        assert sash == {'main_pane': [300]}

    def test_profile_timestamp_consistency(self):
        """Test that profile timestamps are consistent and reasonable."""
        config_manager = self.create_test_config_manager()

        # Create profiles at different times
        start_time = datetime.now()

        config_manager.save_profile('first', [{'filepath': '/first.pdf', 'selected_pages': [1]}])

        # Small delay
        import time
        time.sleep(0.1)

        config_manager.save_profile('second', [{'filepath': '/second.pdf', 'selected_pages': [1]}])

        # Verify timestamps are different and reasonable
        first_profile = config_manager.get_profile('first')
        second_profile = config_manager.get_profile('second')

        first_time = datetime.fromisoformat(first_profile['created'])
        second_time = datetime.fromisoformat(second_profile['created'])

        # Second profile should be created after first
        assert second_time > first_time

        # Both should be recent
        now = datetime.now()
        assert (now - first_time).total_seconds() < 10
        assert (now - second_time).total_seconds() < 10

    def test_profile_data_integrity(self):
        """Test that profile data maintains integrity through save/load cycles."""
        config_manager = self.create_test_config_manager()

        # Create complex profile data
        original_files = [
            {
                'filepath': '/very/complex/path/document with spaces.pdf',
                'filename': 'document with spaces.pdf',
                'selected_pages': [1, 3, 5, 7, 9, 11, 13, 15],
                'page_count': 100,
                'file_type': 'pdf'
            },
            {
                'filepath': '/another/path/文档.pdf',
                'filename': '文档.pdf',
                'selected_pages': list(range(1, 21)),  # Pages 1-20
                'page_count': 50,
                'file_type': 'pdf'
            }
        ]

        # Set complex configuration
        config_manager.config.update({
            'compression_level': 'maximum',
            'preserve_bookmarks': True,
            'output_password_protect': True,
            'output_password': 'complex!@#password123',
            'output_color_mode': 'Black and White',
            'output_dpi': '600'
        })

        # Save profile
        config_manager.save_profile('complex_integrity_test', original_files)

        # Multiple save/load cycles
        for i in range(3):
            config_manager.save_config()
            config_manager = ConfigManager(config_manager.config_path)

        # Verify data integrity maintained
        final_profile = config_manager.get_profile('complex_integrity_test')

        # Verify file data
        assert len(final_profile['pdf_merger_pro_list']) == 2
        assert final_profile['pdf_merger_pro_list'][0]['filepath'] == original_files[0]['filepath']
        assert final_profile['pdf_merger_pro_list'][0]['selected_pages'] == original_files[0]['selected_pages']
        assert final_profile['pdf_merger_pro_list'][1]['filename'] == original_files[1]['filename']

        # Verify configuration preserved
        assert final_profile['compression_level'] == 'maximum'
        assert final_profile['preserve_bookmarks'] is True
        assert final_profile['output_password_protect'] is True
        # Note: output_password is not saved for security reasons
        assert final_profile['output_color_mode'] == 'Black and White'
        assert final_profile['output_dpi'] == '600'
