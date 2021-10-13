from typing import List
import pyatspi
import threading


CLICKABLE_OBJECT_CLASSES = ['radio_button', 'check_box', 'push_button', 'combo_box', 'toggle_button', 'radio_menu_item']
ACTIONABLE_STATES = [pyatspi.STATE_VISIBLE, pyatspi.STATE_SHOWING]
ACTIONABLE_STATES_SET = set(pyatspi.StateSet(*ACTIONABLE_STATES).getStates())
ACTIVE_STATES = [pyatspi.STATE_ACTIVE]
ACTIVE_STATES_SET = set(ACTIVE_STATES)
SELECTABLE_STATES = [pyatspi.STATE_SELECTABLE]
SELECTABLE_STATES_SET = set(SELECTABLE_STATES)


class Registry(object):
    def __init__(self, logger):
        self.actionable_objects = []
        self.listeners = []
        self.logger = logger
        self.registry = pyatspi.Registry()
    

    def active_window(self):
        desktop = self.registry.getDesktop(0)

        for app in desktop:
            app_state_set = app.getState().getStates()
            if pyatspi.STATE_DEFUNCT in app_state_set:
                self.logger.debug({'message': 'App defunct.', 'app': app})
                continue

            self.logger.debug({'message': 'Found app.', 'app': app, 'states': app_state_set})

            if ACTIONABLE_STATES_SET.issubset(app_state_set):
                self.logger.debug({'message': 'App visible and showing', 'app': app})

                for window in app:
                    window_state_set = window.getState().getStates()
                    self.logger.debug({'message': 'Found app window.', 'window': window, 'states': window_state_set})

                    if ACTIVE_STATES_SET.issubset(window_state_set):
                        self.logger.debug({'message': 'App window is active.', 'app': app, 'window': window, 'role': window.getRoleName(), 'states': window.getState().getStates()})
                        return Window(self.logger, window)


class ActionableObject:
    def __init__(self, object, component):
        self.object = object
        self.component = component
        self.role = object.getRole()

        self.position = component.getPosition(0)
        self.size = component.getSize()

    def do_action(self):
        raise NotImplementedError()


# TODO(bkd): semantics that aren't awful 
class ActionObject(ActionableObject):
    def __init__(self, object, component, action, action_index):
        ActionableObject.__init__(self, object, component)
        self.action = action
        self.action_index = action_index

    @staticmethod
    def create(object, component, action, click_ancestor=False) -> List[ActionableObject]:
        action_objects = []
        action_names = [action.getName(i) for i in range(0, action.nActions)]
        for action_index, action_name in enumerate(action_names):
            if action_name == 'click':
                action_objects.append(ClickableObject(object, component, action, action_index))
            elif action_name == 'press':
                action_objects.append(PressableObject(object, component, action, action_index))
            elif action_name == 'clickAncestor' and click_ancestor:
                action_objects.append(SelectableObject(object, component, action, action_index))

        return action_objects

    def do_action(self):
        self.action.doAction(self.action_index)    


class ClickableObject(ActionObject):
    pass


class PressableObject(ActionObject):
    pass


class SelectableObject(ActionObject):
    pass
    # TODO(bkd): this didn't work, so I'm using clickAncestor
    # def do_action(self):
    #     self.selection.selectChild(self.object.getIndexInParent())


class Window():
    def __init__(self, logger, window):
        self.logger = logger
        self.logger.debug({'message': 'Introspecting window.', 'window': window})
        self.window = window
        self.actionable_objects = []
        self.load_actionable_objects(0, window)
        self.logger.debug({'message': 'Finished introspecting window.', 'window': window})

    def filter_actionable_objects(self, actionable_object_types):
        return list(filter(lambda x: type(x) in actionable_object_types, self.actionable_objects))

    def load_actionable_objects(self, index, root):
        root_states_set = set(root.getState().getStates())

        self.logger.debug({'message': 'Introspecting actionable object.', 'window': self.window, 'root': root, 'role': root.getRole(), 'states': root_states_set})

        component = root.queryComponent()

        if ACTIONABLE_STATES_SET.issubset(root_states_set):
            try:
                action = root.queryAction()

                # TODO(bkd): this feels like a hack
                click_ancestor = [False, True][set([pyatspi.STATE_SELECTABLE]).issubset(root_states_set)]

                self.actionable_objects.extend(ActionObject.create(root, component, action, click_ancestor))
            except NotImplementedError:
                pass
            except Exception as error:
                self.logger.error({'message': 'Error getting action.', 'error': error})

        for child in root:
            if child:
                self.load_actionable_objects(index + 1, child)
