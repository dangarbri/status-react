from tests import marks, pair_code, common_password
from tests.base_test_case import SingleDeviceTestCase, MultipleDeviceTestCase
from views.sign_in_view import SignInView
from tests.users import basic_user, transaction_senders


class TestCreateAccount(SingleDeviceTestCase):

    @marks.testrail_id(5742)
    @marks.medium
    def test_keycard_interruption_creating_onboarding_flow(self):
        sign_in = SignInView(self.driver)

        sign_in.just_fyi('Cancel on PIN code setup stage')
        sign_in.accept_tos_checkbox.enable()
        sign_in.get_started_button.click()
        sign_in.generate_key_button.click()
        username = sign_in.first_username_on_choose_chat_name.text
        sign_in.next_button.click()
        keycard_flow = sign_in.keycard_storage_button.click()
        keycard_flow.next_button.click()
        keycard_flow.begin_setup_button.click()
        keycard_flow.connect_card_button.wait_and_click()
        keycard_flow.enter_another_pin()
        keycard_flow.cancel_button.click()

        sign_in.just_fyi('Cancel from Confirm seed phrase: initialized + 1 pairing slot is used')
        keycard_flow.begin_setup_button.click()
        keycard_flow.enter_default_pin()
        keycard_flow.enter_default_pin()
        seed_phrase = keycard_flow.get_seed_phrase()
        keycard_flow.confirm_button.click()
        keycard_flow.yes_button.click()
        keycard_flow.cancel_button.click()
        if not keycard_flow.element_by_text_part('Back up seed phrase').is_element_displayed():
            self.driver.fail('On canceling setup from Confirm seed phrase was not redirected to expected screen')

        sign_in.just_fyi('Cancel from Back Up seed phrase: initialized + 1 pairing slot is used')
        keycard_flow.cancel_button.click()
        keycard_flow.begin_setup_button.click()
        keycard_flow.element_by_translation_id("back-up-seed-phrase").wait_for_element(10)
        new_seed_phrase = keycard_flow.get_seed_phrase()
        if new_seed_phrase != seed_phrase:
            self.errors.append('Another seed phrase is shown after cancelling setup during Back up seed phrase')
        keycard_flow.backup_seed_phrase()
        keycard_flow.enter_default_pin()
        for element in sign_in.maybe_later_button, sign_in.lets_go_button:
            element.wait_for_visibility_of_element(30)
            element.click()
        sign_in.profile_button.wait_for_visibility_of_element(30)

        sign_in.just_fyi('Check username and relogin')
        profile = sign_in.get_profile_view()
        public_key, real_username = profile.get_public_key_and_username(return_username=True)
        if real_username != username:
            self.errors.append('Username was changed after interruption of creating account')
        profile.logout()
        home = sign_in.sign_in(keycard=True)
        if not home.wallet_button.is_element_displayed(10):
            self.errors.append("Failed to login to Keycard account")
        self.errors.verify_no_errors()

    @marks.testrail_id(6246)
    @marks.medium
    @marks.flaky
    def test_keycard_interruption_access_key_onboarding_flow(self):
        sign_in = SignInView(self.driver)
        sign_in.accept_tos_checkbox.enable()
        sign_in.get_started_button.click()

        sign_in.access_key_button.click()
        sign_in.enter_seed_phrase_button.click()
        sign_in.seedphrase_input.click()
        sign_in.seedphrase_input.set_value(basic_user['passphrase'])
        sign_in.next_button.click()
        sign_in.reencrypt_your_key_button.click()
        keycard_flow = sign_in.keycard_storage_button.click()

        sign_in.just_fyi('Cancel on PIN code setup stage')
        keycard_flow.next_button.click()
        keycard_flow.begin_setup_button.click()
        keycard_flow.connect_card_button.wait_and_click()
        keycard_flow.enter_another_pin()
        keycard_flow.cancel_button.click()

        sign_in.just_fyi('Finish setup and relogin')
        keycard_flow.begin_setup_button.click()
        keycard_flow.enter_default_pin()
        keycard_flow.enter_default_pin()
        for element in sign_in.maybe_later_button, sign_in.lets_go_button:
            element.wait_for_visibility_of_element(30)
            element.click()
        sign_in.profile_button.wait_for_visibility_of_element(30)
        public_key, default_username = sign_in.get_public_key_and_username(return_username=True)
        profile_view = sign_in.get_profile_view()
        if public_key != basic_user['public_key']:
            self.errors.append('Public key %s does not match expected' % public_key)
        if default_username != basic_user['username']:
            self.errors.append('Default username %s does not match expected' % default_username)
        profile_view.logout()
        home = sign_in.sign_in(keycard=True)
        if not home.wallet_button.is_element_displayed(10):
            self.errors.append("Failed to login to Keycard account")
        self.errors.verify_no_errors()

    @marks.testrail_id(6243)
    @marks.medium
    def test_keycard_can_recover_keycard_account_offline_and_add_watch_only_acc(self):
        sign_in = SignInView(self.driver)
        sign_in.toggle_airplane_mode()

        sign_in.just_fyi('Recover multiaccount offline')
        sign_in.accept_tos_checkbox.enable()
        sign_in.get_started_button.click_until_presence_of_element(sign_in.access_key_button)
        sign_in.access_key_button.click()
        sign_in.recover_with_keycard_button.click()
        keycard_view = sign_in.begin_recovery_button.click()
        keycard_view.connect_pairing_card_button.click()
        keycard_view.pair_code_input.set_value(pair_code)
        keycard_view.confirm()
        keycard_view.enter_default_pin()
        sign_in.maybe_later_button.click_until_presence_of_element(sign_in.lets_go_button)
        sign_in.lets_go_button.click_until_absense_of_element(sign_in.lets_go_button)
        sign_in.home_button.wait_for_visibility_of_element(30)
        wallet_view = sign_in.wallet_button.click()

        sign_in.just_fyi('Relogin offline')
        self.driver.close_app()
        self.driver.launch_app()
        sign_in.sign_in(keycard=True)
        if not sign_in.home_button.is_element_displayed(10):
            self.driver.fail('Keycard user is not logged in')

        sign_in.just_fyi('Turn off airplane mode and turn on cellular network')
        sign_in.toggle_airplane_mode()
        sign_in.toggle_mobile_data()
        sign_in.element_by_text_part('Stop syncing').wait_and_click(60)
        sign_in.wallet_button.click()
        if not wallet_view.element_by_text_part('LXS').is_element_displayed():
            self.errors.append('Token balance is not fetched while on cellular network!')

        wallet_view.just_fyi('Add watch-only account when on cellular network')
        wallet_view.add_account_button.click()
        wallet_view.add_watch_only_address_button.click()
        wallet_view.enter_address_input.send_keys(basic_user['address'])
        account_name = 'watch-only'
        wallet_view.account_name_input.send_keys(account_name)
        wallet_view.add_account_generate_account_button.click()
        account_button = wallet_view.get_account_by_name(account_name)
        if not account_button.is_element_displayed():
            self.driver.fail('Account was not added')

        wallet_view.just_fyi('Check that balance is changed after go back to WI-FI')
        sign_in.toggle_mobile_data()
        for asset in ('ADI', 'STT'):
            wallet_view.asset_by_name(asset).scroll_to_element()
            wallet_view.wait_balance_is_changed(asset, wait_time=60)

        wallet_view.just_fyi('Delete watch-only account')
        wallet_view.get_account_by_name(account_name).click()
        wallet_view.get_account_options_by_name(account_name).click()
        wallet_view.account_settings_button.click()
        wallet_view.delete_account_button.click()
        wallet_view.yes_button.click()
        if wallet_view.get_account_by_name(account_name).is_element_displayed(20):
            self.errors.append('Account was not deleted')

        self.errors.verify_no_errors()

    @marks.testrail_id(6311)
    @marks.medium
    @marks.transaction
    def test_same_seed_added_inside_multiaccount_and_keycard(self):
        sign_in = SignInView(self.driver)
        recipient = "0x" + transaction_senders['ETH_7']['address']
        user = transaction_senders['ETH_ADI_STT_3']

        sign_in.just_fyi('Restore keycard multiaccount and logout')
        sign_in.recover_access(passphrase=user['passphrase'], keycard=True)
        profile_view = sign_in.profile_button.click()
        profile_view.logout()

        sign_in.just_fyi('Create new multiaccount')
        sign_in.close_button.click()
        sign_in.your_keys_more_icon.click()
        sign_in.generate_new_key_button.click()
        sign_in.next_button.click()
        sign_in.next_button.click()
        sign_in.create_password_input.set_value(common_password)
        sign_in.next_button.click()
        sign_in.confirm_your_password_input.set_value(common_password)
        sign_in.next_button.click()
        sign_in.maybe_later_button.click_until_presence_of_element(sign_in.lets_go_button)
        sign_in.lets_go_button.click()

        sign_in.just_fyi('Add to wallet seed phrase for restored multiaccount')
        wallet = sign_in.wallet_button.click()
        wallet.add_account_button.click()
        wallet.enter_a_seed_phrase_button.click()
        wallet.enter_your_password_input.send_keys(common_password)
        account_name = 'subacc'
        wallet.account_name_input.send_keys(account_name)
        wallet.enter_seed_phrase_input.set_value(user['passphrase'])
        wallet.add_account_generate_account_button.click()
        wallet.get_account_by_name(account_name).click()

        sign_in.just_fyi('Send transaction from added account and log out')
        transaction_amount_added = wallet.get_unique_amount()
        wallet.send_transaction(from_main_wallet=False, amount=transaction_amount_added, recipient=recipient,
                                sign_transaction=True)
        wallet.profile_button.click()
        profile_view.logout()

        sign_in.just_fyi('Login to keycard account and send another transaction')
        sign_in.back_button.click()
        sign_in.sign_in(position=2, keycard=True)
        sign_in.wallet_button.click()
        wallet.wait_balance_is_changed('ETH')
        transaction_amount_keycard = wallet.get_unique_amount()
        wallet.send_transaction(amount=transaction_amount_keycard, recipient=recipient, keycard=True,
                                sign_transaction=True)

        for amount in [transaction_amount_keycard, transaction_amount_added]:
            sign_in.just_fyi("Checking '%s' tx" % amount)
            self.network_api.find_transaction_by_unique_amount(user['address'], amount)

        self.errors.verify_no_errors()

    @marks.testrail_id(695841)
    @marks.medium
    def test_keycard_settings_pin_puk_pairing(self):
        sign_in = SignInView(self.driver)
        seed = basic_user['passphrase']
        home = sign_in.recover_access(passphrase=seed, keycard=True)
        profile = home.profile_button.click()

        home.just_fyi("Checking changing PIN")
        profile.keycard_button.scroll_and_click()
        keycard = profile.change_pin_button.click()
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_default_pin()
        if not keycard.element_by_translation_id("new-pin-description").is_element_displayed():
            self.driver.fail("Screen for setting new pin is not shown!")
        [keycard.enter_another_pin() for _ in range(2)]
        if not keycard.element_by_translation_id("pin-changed").is_element_displayed(30):
            self.driver.fail("Popup about successful setting new PIN is not shown!")
        keycard.ok_button.click()

        home.just_fyi("Checking changing PUK with new PIN")
        profile.change_puk_button.click()
        keycard.enter_another_pin()
        if not keycard.element_by_translation_id("new-puk-description").is_element_displayed():
            self.driver.fail("Screen for setting new puk is not shown!")
        [keycard.one_button.click() for _ in range(12)]
        if not keycard.element_by_translation_id("repeat-puk").is_element_displayed():
            self.driver.fail("Confirmation screen for setting new puk is not shown!")
        [keycard.one_button.click() for _ in range(12)]
        if not keycard.element_by_translation_id("puk-changed").is_element_displayed(30):
            self.driver.fail("Popup about successful setting new PUK is not shown!")
        keycard.ok_button.click()

        home.just_fyi("Checking setting pairing with new PIN")
        profile.change_pairing_code_button.click()
        keycard.enter_another_pin()
        sign_in.create_password_input.set_value(common_password)
        sign_in.confirm_your_password_input.set_value(common_password + "1")
        if not keycard.element_by_translation_id("pairing-code_error1").is_element_displayed():
            self.errors.append("No error is shown when pairing codes don't match")
        sign_in.confirm_your_password_input.delete_last_symbols(1)
        sign_in.element_by_translation_id("change-pairing").click()
        if not keycard.element_by_translation_id("pairing-changed").is_element_displayed(30):
            self.driver.fail("Popup about successful setting new pairing is not shown!")
        keycard.ok_button.click()

        home.just_fyi("Checking backing up keycard")
        profile.create_keycard_backup_button.scroll_and_click()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.return_card_to_factory_settings_checkbox.enable()
        keycard.begin_setup_button.click()
        keycard.yes_button.wait_and_click()
        [keycard.enter_another_pin() for _ in range(2)]
        keycard.element_by_translation_id("keycard-backup-success-title").wait_for_element(30)
        keycard.ok_button.click()

        self.errors.verify_no_errors()

    @marks.testrail_id(695851)
    @marks.medium
    def test_keycard_frozen_card_flows(self):
        sign_in = SignInView(self.driver)
        seed = basic_user['passphrase']
        home = sign_in.recover_access(passphrase=seed, keycard=True)
        profile = home.profile_button.click()
        profile.keycard_button.scroll_and_click()

        home.just_fyi('Set new PUK')
        keycard = profile.change_puk_button.click()
        keycard.enter_default_pin()
        [keycard.enter_default_puk() for _ in range(2)]
        keycard.ok_button.click()

        home.just_fyi("Checking reset with PUK when logged in")
        keycard = profile.change_pin_button.click()
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_another_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_another_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed(30):
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("keycard-is-frozen-reset").click()
        keycard.enter_another_pin()
        home.element_by_text_part('2/2').wait_for_element(20)
        keycard.enter_another_pin()
        home.element_by_translation_id("enter-puk-code").click()
        keycard.enter_default_puk()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(20)
        home.profile_button.double_click()
        profile.logout()

        home.just_fyi("Checking reset with PUK when logged out")
        keycard.enter_default_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_default_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_default_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("keycard-is-frozen-reset").click()
        keycard.enter_another_pin()
        home.element_by_text_part('2/2').wait_for_element(20)
        keycard.enter_another_pin()
        home.element_by_translation_id("enter-puk-code").click()
        keycard.enter_default_puk()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(20)
        home.element_by_translation_id("open").click()

        home.just_fyi("Checking reset with seed when logged in")
        profile = home.profile_button.click()
        profile.keycard_button.scroll_and_click()
        profile.change_pin_button.click()
        keycard.enter_default_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_default_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_default_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("dismiss").click()
        profile.profile_button.double_click()
        profile.keycard_button.scroll_and_click()
        profile.change_pin_button.click()
        keycard.enter_default_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed(30):
            self.driver.fail("No reset card flow is shown for frozen card")
        home.element_by_translation_id("keycard-is-frozen-factory-reset").click()
        sign_in.seedphrase_input.set_value(transaction_senders['A']['passphrase'])
        sign_in.next_button.click()
        if not home.element_by_translation_id("seed-key-uid-mismatch").is_element_displayed():
            self.driver.fail("No popup about mismatch in seed phrase is shown!")
        home.element_by_translation_id("try-again").click()
        sign_in.seedphrase_input.clear()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.begin_setup_button.click()
        keycard.yes_button.click()
        keycard.enter_default_pin()
        home.element_by_translation_id("intro-wizard-title5").wait_for_element(20)
        keycard.enter_default_pin()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(30)
        home.ok_button.click()
        profile.profile_button.double_click()
        profile.logout()

        home.just_fyi("Checking reset with seed when logged out")
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_another_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_another_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")

        sign_in.element_by_translation_id("keycard-is-frozen-factory-reset").click()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.begin_setup_button.click()
        keycard.yes_button.click()
        keycard.enter_default_pin()
        home.element_by_translation_id("intro-wizard-title5").wait_for_element(20)
        keycard.enter_default_pin()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(30)
        home.ok_button.click()
        keycard.enter_default_pin()
        home.home_button.wait_for_element(30)

    @marks.testrail_id(695852)
    @marks.medium
    def test_keycard_blocked_card_lost_or_frozen_flows(self):
        sign_in = SignInView(self.driver)
        seed = basic_user['passphrase']
        home = sign_in.recover_access(passphrase=seed, keycard=True)
        profile = home.profile_button.click()
        profile.keycard_button.scroll_and_click()

        home.just_fyi("Checking blocked card screen when entering 3 times invalid PIN + 5 times invalid PUK")
        keycard = profile.change_pin_button.click()
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_another_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_another_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("keycard-is-frozen-reset").click()
        keycard.enter_another_pin()
        home.element_by_text_part('2/2').wait_for_element(20)
        keycard.enter_another_pin()
        home.element_by_translation_id("enter-puk-code").click()

        for i in range(1, 4):
            keycard.enter_default_puk()
            sign_in.wait_for_element_starts_with_text('%s attempts left' % str(5 - i))
            i += 1
        keycard.enter_default_puk()
        sign_in.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_default_puk()
        keycard.element_by_translation_id("keycard-is-blocked-title").wait_for_element(30)
        keycard.close_button.click()
        if not keycard.element_by_translation_id("keycard-blocked").is_element_displayed():
            self.errors.append("In keycard settings there is no info that card is blocked")
        keycard.back_button.click()
        profile.logout()

        home.just_fyi("Check blocked card when user is logged out and use lost or frozen to restore access")
        keycard.enter_another_pin()
        keycard.element_by_translation_id("keycard-is-blocked-title").wait_for_element(30)
        keycard.element_by_translation_id("keycard-recover").click()
        keycard.yes_button.click()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.begin_setup_button.click()
        keycard.yes_button.click()
        keycard.enter_default_pin()
        home.element_by_translation_id("intro-wizard-title5").wait_for_element(20)
        keycard.enter_default_pin()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(30)
        home.ok_button.click()
        keycard.enter_default_pin()
        home.home_button.wait_for_element(30)

        self.errors.verify_no_errors()

