import sublime_plugin


class ACTriggerWorkaroundListener(sublime_plugin.EventListener):

    """Work around an issue
    where auto complete triggers aren't respected
    after a snippet from an auto-match has been inserted.
    Manually apply the logic when that happened.
    """

    def on_post_text_command(self, view, command, args):
        if "PackageDev" not in view.settings().get('syntax', ""):
            return

        if command == 'insert_snippet':
            triggers = view.settings().get('auto_complete_triggers', [])
            pt = view.sel()[0].begin() - 1
            for trigger in triggers:
                selector = trigger.get('selector')
                selector_matches = not selector or view.match_selector(pt, selector)
                chars = trigger.get('characters')
                chars_match = not chars or view.substr(pt) in chars
                if selector_matches and chars_match:
                    view.run_command('auto_complete')
                    return
