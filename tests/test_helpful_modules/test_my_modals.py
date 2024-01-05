import unittest
import unittest.mock
from helpful_modules import my_modals
import disnake
from helpful_modules import threads_or_useful_funcs
import typing

class TestMyModals(unittest.IsolatedAsyncioTestCase):
    async def test_default_init(self):
        modal_2 = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction),
            components=[],
        )
        with self.assertRaises(NotImplementedError):
            await modal_2.callback(unittest.mock.AsyncMock(spec=disnake.ModalInteraction))
        self.assertTrue(await modal_2._check(unittest.mock.AsyncMock(spec=int)))

    @unittest.mock.patch("builtins.print")
    async def test_custom_callback_called_on_interaction(self, mock_print):
        # Arrange
        async def custom_callback(modal, inter, *args):
            print(args) # you can't actually return anything since it doesn't get returned
        async def custom_check(*args, **kwargs):
            return True
        interaction = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        modal = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=interaction,
            components=[],
            check=custom_check,
            callback=custom_callback,
            extra_args=["arg1", "arg2"]
        )


        # Act
        result = await modal.callback(interaction)

        # Assert
        mock_print.assert_called_with(("arg1", "arg2"))

        self.assertEqual(result, None)

    # @unittest.mock.patch("helpful_modules.threads_or_useful_funcs.base_on_error")
    async def test_on_error_called_with_correct_arguments(self):
        # Arrange
        # mock_base_on_error.side_effect = lambda *args, **kwargs: {"content": "An error occurred!"}
        interaction = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        modal = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=interaction,
            components=[],
            on_error=my_modals.MyModal.on_error
        )

        try:

            err = Exception("Test Exception")
            raise err
        except Exception as error:
            actual_return_stuff = await threads_or_useful_funcs.base_on_error(interaction, error)
            # Act
            await modal.on_error(error, interaction)

            # Assert
            #mock_base_on_error.assert_awaited_with(error, interaction)

            interaction.send.assert_awaited_once_with(
                **actual_return_stuff
            )

    async def test_modal_timeout_sends_correct_message(self):
        # Arrange
        interaction = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        modal = my_modals.MyModal(
            timeout=-1.0,
            title="HAHA!",
            custom_id="2171828384858",
            inter=interaction,
            components=[]
        )


        # Act
        await modal.on_timeout()

        # Assert
        interaction.send.assert_awaited_once_with("You didn't submit the modal fast enough!")

if __name__ == "__main__":
    unittest.main()
