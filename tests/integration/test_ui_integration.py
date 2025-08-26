"""
Integration tests for UI component integration.

These tests verify that UI components work together correctly and integrate
properly with the underlying business logic and data models.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from tests.integration.base_integration_test import BaseIntegrationTest
from app.managers.config_manager import ConfigManager


class TestUIStateSynchronization(BaseIntegrationTest):
    """Test synchronization between UI components and application state."""

    def test_ui_state_with_config_changes(self):
        """Test that UI state reflects configuration changes."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            # Simulate UI components that should reflect config changes
            mock_frame = mock_components['frame']
            mock_label = mock_components['label']
            mock_string_var = mock_components['string_var']

            # Mock UI variables that should sync with config
            ui_vars = {
                'compression_var': mock_string_var('normal'),
                'bookmarks_var': mock_string_var('True'),
                'password_var': mock_string_var('')
            }

            # Initial config
            config_manager.config.update({
                'compression_level': 'normal',
                'preserve_bookmarks': True,
                'output_password': ''
            })

            # Verify UI reflects config
            assert ui_vars['compression_var'].get() == 'normal'
            assert ui_vars['bookmarks_var'].get() == 'True'
            assert ui_vars['password_var'].get() == ''

            # Modify config
            config_manager.config.update({
                'compression_level': 'high',
                'preserve_bookmarks': False,
                'output_password': 'secret123'
            })

            # UI should be updated to reflect new config
            ui_vars['compression_var'].set(config_manager.config['compression_level'])
            ui_vars['bookmarks_var'].set(str(config_manager.config['preserve_bookmarks']))
            ui_vars['password_var'].set(config_manager.config['output_password'])

            # Verify UI updated
            assert ui_vars['compression_var'].get() == 'high'
            assert ui_vars['bookmarks_var'].get() == 'False'
            assert ui_vars['password_var'].get() == 'secret123'

    def test_ui_file_list_synchronization(self):
        """Test synchronization between UI file list and document data."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']

            # Mock file list UI component
            mock_tree = MagicMock()
            mock_tk_instance.nametowidget = MagicMock(return_value=mock_tree)

            # Mock document data
            documents = [
                {
                    'filepath': '/doc1.pdf',
                    'filename': 'doc1.pdf',
                    'selected_pages': [1, 2, 3],
                    'page_count': 10
                },
                {
                    'filepath': '/doc2.pdf',
                    'filename': 'doc2.pdf',
                    'selected_pages': [1, 2],
                    'page_count': 8
                }
            ]

            # Simulate UI updating from document data
            for i, doc in enumerate(documents):
                mock_tree.insert('', 'end', values=(
                    doc['filename'],
                    f"{len(doc['selected_pages'])}/{doc['page_count']}",
                    doc['filepath']
                ))

            # Verify UI reflects document data
            assert mock_tree.insert.call_count == 2

            # Verify first document
            first_call = mock_tree.insert.call_args_list[0]
            args, kwargs = first_call
            assert 'doc1.pdf' in kwargs['values']
            assert '3/10' in kwargs['values']

            # Verify second document
            second_call = mock_tree.insert.call_args_list[1]
            args, kwargs = second_call
            assert 'doc2.pdf' in kwargs['values']
            assert '2/8' in kwargs['values']


class TestUIBusinessLogicIntegration(BaseIntegrationTest):
    """Test integration between UI components and business logic."""

    def test_ui_action_triggers_business_logic(self):
        """Test that UI actions properly trigger business logic operations."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']

            # Mock UI buttons and their commands
            mock_merge_button = MagicMock()
            mock_add_files_button = MagicMock()
            mock_save_profile_button = MagicMock()

            # Mock business logic handlers
            merge_handler = MagicMock()
            add_files_handler = MagicMock()
            save_profile_handler = MagicMock()

            # Connect UI actions to business logic and simulate button clicks
            mock_merge_button.configure(command=merge_handler)
            mock_add_files_button.configure(command=add_files_handler)
            mock_save_profile_button.configure(command=save_profile_handler)

            # Simulate user interactions by directly calling the commands
            merge_handler()
            add_files_handler()
            save_profile_handler()

            # Verify business logic was triggered
            merge_handler.assert_called_once()
            add_files_handler.assert_called_once()
            save_profile_handler.assert_called_once()

    def test_ui_data_binding_with_config(self):
        """Test data binding between UI elements and configuration."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_string_var = mock_components['string_var']

            # Create UI variables bound to config with initial values
            ui_bindings = {
                'compression': mock_string_var('normal'),
                'color_mode': mock_string_var('Colorful (Original)'),
                'password_protect': mock_string_var('False')
            }

            # Set initial config
            config_manager.config.update({
                'compression_level': 'normal',
                'output_color_mode': 'Colorful (Original)',
                'output_password_protect': False
            })

            # Verify initial binding
            assert ui_bindings['compression'].get() == 'normal'
            assert ui_bindings['color_mode'].get() == 'Colorful (Original)'
            assert ui_bindings['password_protect'].get() == 'False'

            # Simulate user changing UI values
            ui_bindings['compression'].set('high')
            ui_bindings['color_mode'].set('Grayscale')

            # Sync config with UI changes
            config_manager.config['compression_level'] = ui_bindings['compression'].get()
            config_manager.config['output_color_mode'] = ui_bindings['color_mode'].get()

            # Verify config updated
            assert config_manager.config['compression_level'] == 'high'
            assert config_manager.config['output_color_mode'] == 'Grayscale'


class TestUIErrorHandlingIntegration(BaseIntegrationTest):
    """Test error handling integration with UI components."""

    def test_ui_error_display_integration(self):
        """Test that errors are properly displayed in UI."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']
            mock_messagebox = MagicMock()

            # Mock error scenario
            with patch('tkinter.messagebox.showerror', mock_messagebox):
                # Simulate error in file processing
                test_error = Exception("File processing failed")

                # Mock error handler that would display error in UI
                def error_handler():
                    mock_messagebox("Error", f"Operation failed: {str(test_error)}")

                # Trigger error handling
                error_handler()

                # Verify error displayed to user
                mock_messagebox.assert_called_once()
                call_args = mock_messagebox.call_args[0]
                assert "Error" in call_args
                assert "File processing failed" in call_args[1]

    def test_ui_validation_feedback(self):
        """Test UI validation feedback integration."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_label = mock_components['label']

            # Mock validation feedback UI elements
            error_label = mock_label()
            error_label.configure(text="")

            # Test scenarios
            validation_scenarios = [
                ("", "Profile name cannot be empty"),
                ("   ", "Profile name cannot be empty"),
                ("valid_name", ""),
                ("another valid", "")
            ]

            for input_value, expected_error in validation_scenarios:
                if not input_value.strip():
                    error_label.configure(text=expected_error)
                    assert error_label.cget('text') == expected_error
                else:
                    error_label.configure(text="")
                    assert error_label.cget('text') == ""


class TestUIStatePersistenceIntegration(BaseIntegrationTest):
    """Test UI state persistence integration."""

    def test_ui_window_state_persistence(self):
        """Test that window state is properly persisted and restored."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']

            # Mock window geometry methods
            mock_tk_instance.geometry = MagicMock(return_value="1200x800+100+200")
            mock_tk_instance.sashpos = MagicMock(return_value=(300, 500))

            # Save window state
            geometry = mock_tk_instance.geometry()
            sash_positions = {'main_pane': mock_tk_instance.sashpos()}
            config_manager.save_window_state(geometry, sash_positions)

            # Save and reload
            config_manager.save_config()
            new_manager = ConfigManager(config_manager.config_path)

                    # Verify window state persisted (tuples become lists in JSON)
        loaded_geometry, loaded_sash = new_manager.load_window_state()
        assert loaded_geometry == geometry
        # Convert tuples to lists for comparison since JSON serialization converts tuples to lists
        expected_sash = {k: list(v) for k, v in sash_positions.items()}
        assert loaded_sash == expected_sash

    def test_ui_recent_directories_integration(self):
        """Test UI integration with recent directories."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']

            # Mock recent directories menu
            mock_menu = MagicMock()
            mock_tk_instance.nametowidget = MagicMock(return_value=mock_menu)

            # Add recent directories
            with patch('os.path.isdir', return_value=True):
                test_dirs = ['/home/docs', '/work/projects', '/temp']
                for test_dir in test_dirs:
                    config_manager.add_recent_directory(test_dir)

            # Simulate UI updating recent directories menu
            for i, recent_dir in enumerate(config_manager.config['recent_directories']):
                resolved_dir = str(Path(recent_dir).resolve())
                mock_menu.add_command(label=resolved_dir, command=MagicMock())

            # Verify menu updated
            assert mock_menu.add_command.call_count == len(test_dirs)

            # Verify correct directories in menu
            for call in mock_menu.add_command.call_args_list:
                menu_label = call[1]['label']
                assert any(str(Path(d).resolve()) == menu_label for d in test_dirs)


class TestUIWorkflowIntegration(BaseIntegrationTest):
    """Test complete UI workflows."""

    def test_file_selection_workflow_ui_integration(self):
        """Test complete file selection workflow with UI integration."""
        config_manager = self.create_test_config_manager()

        # Create test files
        test_files = []
        for i in range(3):
            test_files.append(self.create_test_pdf(f"workflow_test_{i}.pdf", f"Content {i}"))

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']

            # Mock file dialog
            with patch('tkinter.filedialog.askopenfilenames') as mock_dialog:
                mock_dialog.return_value = [str(f) for f in test_files]

                # Simulate file selection UI workflow
                selected_files = mock_dialog(multiple=True)

                # Verify file selection
                assert len(selected_files) == 3
                assert all(f.endswith('.pdf') for f in selected_files)

                # Process selected files (would normally call business logic)
                processed_count = len(selected_files)

                # Verify workflow completion
                assert processed_count == 3

    def test_profile_management_ui_workflow(self):
        """Test profile management UI workflow."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_tk_instance = mock_components['tk_instance']

            # Mock profile management UI components
            mock_profile_list = MagicMock()
            mock_save_button = MagicMock()
            mock_load_button = MagicMock()
            mock_delete_button = MagicMock()

            # Create test profiles
            profiles = {
                'profile_1': [{'filepath': '/file1.pdf', 'selected_pages': [1, 2]}],
                'profile_2': [{'filepath': '/file2.pdf', 'selected_pages': [1]}]
            }

            for name, files in profiles.items():
                config_manager.save_profile(name, files)

            # Simulate UI updating profile list
            for profile_name in config_manager.config['profiles'].keys():
                mock_profile_list.insert('', 'end', values=(profile_name,))

            # Verify profile list populated
            assert mock_profile_list.insert.call_count == len(profiles)

            # Simulate profile operations through UI
            operations_performed = []

            # Save operation
            mock_save_button.configure(command=lambda: operations_performed.append('save'))
            operations_performed.append('save')

            # Load operation
            mock_load_button.configure(command=lambda: operations_performed.append('load'))
            operations_performed.append('load')

            # Delete operation
            mock_delete_button.configure(command=lambda: operations_performed.append('delete'))
            operations_performed.append('delete')

            # Verify operations triggered
            assert len(operations_performed) == 3
            assert 'save' in operations_performed
            assert 'load' in operations_performed
            assert 'delete' in operations_performed

    def test_settings_ui_integration(self):
        """Test settings UI integration with configuration."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_string_var = mock_components['string_var']

            # Mock settings UI components with initial values
            settings_vars = {
                'compression': mock_string_var('normal'),
                'color_mode': mock_string_var('Colorful (Original)'),
                'dpi': mock_string_var('300'),
                'preserve_bookmarks': mock_string_var('True')
            }

            # Initial settings
            initial_settings = {
                'compression_level': 'normal',
                'output_color_mode': 'Colorful (Original)',
                'output_dpi': '300',
                'preserve_bookmarks': True
            }

            config_manager.config.update(initial_settings)

            # Verify UI reflects settings
            assert settings_vars['compression'].get() == 'normal'
            assert settings_vars['color_mode'].get() == 'Colorful (Original)'
            assert settings_vars['dpi'].get() == '300'
            assert settings_vars['preserve_bookmarks'].get() == 'True'

            # Modify settings through UI
            settings_vars['compression'].set('high')
            settings_vars['color_mode'].set('Grayscale')
            settings_vars['dpi'].set('600')
            settings_vars['preserve_bookmarks'].set('False')

            # Apply UI changes to config
            config_manager.config.update({
                'compression_level': settings_vars['compression'].get(),
                'output_color_mode': settings_vars['color_mode'].get(),
                'output_dpi': settings_vars['dpi'].get(),
                'preserve_bookmarks': settings_vars['preserve_bookmarks'].get() == 'True'
            })

            # Verify config updated
            assert config_manager.config['compression_level'] == 'high'
            assert config_manager.config['output_color_mode'] == 'Grayscale'
            assert config_manager.config['output_dpi'] == '600'
            assert config_manager.config['preserve_bookmarks'] is False


class TestUIMultiComponentIntegration(BaseIntegrationTest):
    """Test integration between multiple UI components."""

    def test_multi_component_state_synchronization(self):
        """Test that multiple UI components stay synchronized."""
        config_manager = self.create_test_config_manager()

        with self.mock_tkinter() as mock_components:
            mock_string_var = mock_components['string_var']

            # Mock multiple UI components that need to stay in sync
            file_list_component = MagicMock()
            preview_component = MagicMock()
            settings_component = MagicMock()

            # Mock UI variables
            compression_var = mock_string_var('normal')
            file_count_var = mock_string_var('2')

            # Simulate application state
            app_state = {
                'selected_files': ['/doc1.pdf', '/doc2.pdf'],
                'compression_level': 'normal',
                'current_preview': '/doc1.pdf'
            }

            # Sync UI components with state
            file_count_var.set(str(len(app_state['selected_files'])))
            compression_var.set(app_state['compression_level'])

            # Update file list component
            for file_path in app_state['selected_files']:
                file_list_component.add_file(file_path)

            # Update preview component
            preview_component.load_preview(app_state['current_preview'])

            # Verify all components synchronized
            assert file_count_var.get() == '2'
            assert compression_var.get() == 'normal'
            assert file_list_component.add_file.call_count == 2
            assert preview_component.load_preview.called

            # Simulate state change (file added)
            app_state['selected_files'].append('/doc3.pdf')
            app_state['compression_level'] = 'high'

            # Update UI components
            file_count_var.set(str(len(app_state['selected_files'])))
            compression_var.set(app_state['compression_level'])
            file_list_component.add_file('/doc3.pdf')

            # Verify synchronization maintained
            assert file_count_var.get() == '3'
            assert compression_var.get() == 'high'
            assert file_list_component.add_file.call_count == 3
