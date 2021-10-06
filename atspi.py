from typing import List
import pyatspi

CLICKABLE_OBJECT_CLASSES = ['radio_button', 'check_box', 'push_button', 'combo_box', 'toggle_button', 'radio_menu_item']
ACTIONABLE_STATES = [pyatspi.STATE_VISIBLE, pyatspi.STATE_SHOWING]
ACTIONABLE_STATES_SET = set(pyatspi.StateSet(*ACTIONABLE_STATES).getStates())


def get_active_window():
    for app in pyatspi.Registry.getDesktop(0):
        for window in app:
            if window.getState().contains(pyatspi.STATE_ACTIVE):
                return Window(window)


class ActionableObject:
    def __init__(self, object, component):
        self.object = object
        self.component = component
        self.role = object.getRole()

        # if self.role == pyatspi.ROLE_TREE_ITEM:
        #     parent_component = object.parent.getComponent()
        #     self.position = parent_component.getPosition(0)
        #     self.size = parent_component.getSize()
        # else:
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
            elif click_ancestor and action_name == 'clickAncestor':
                action_objects.append(ClickableObject(object, component, action, action_index))

        return action_objects

    def do_action(self):
        self.action.doAction(self.action_index)    


class ClickableObject(ActionObject):
    pass


class PressableObject(ActionObject):
    pass


# TODO(bkd): this didn't work, so I'm using clickAncestor
class SelectableObject(ActionableObject):
    def __init__(self, object, component, selection):
        ActionableObject.__init__(self, object, component)
        self.selection = selection

    def do_action(self):
        self.selection.selectChild(self.object.getIndexInParent())


class Window():
    def __init__(self, window):
        self.window = window
        self.actionable_objects = []
        self.load_actionable_objects(0, window)

    def clickable_objects(self):
        return [actionable_object for actionable_object in self.actionable_objects
                if isinstance(actionable_object, ClickableObject)]

    def pressable_objects(self):
        return [actionable_object for actionable_object in self.actionable_objects
                if isinstance(actionable_object, PressableObject)]

    def selectable_objects(self):
        return [actionable_object for actionable_object in self.actionable_objects
                if isinstance(actionable_object, SelectableObject)]

    def load_actionable_objects(self, index, tree):
        tree_states_set = set(tree.getState().getStates())
        # print('')
        # print('tree', tree)
        # print('states', tree_states_set)

        component = tree.queryComponent()

        if ACTIONABLE_STATES_SET.issubset(tree_states_set):
            # print('role', tree.getRole())

            try:
                action = tree.queryAction()

                # TODO(bkd): this feels like a hack
                click_ancestor = False
                if set([pyatspi.STATE_SELECTABLE]).issubset(tree_states_set):
                    click_ancestor = True

                self.actionable_objects.extend(ActionObject.create(tree, component, action, click_ancestor))
            except NotImplementedError:
                pass
            except Exception as error:
                print('Error getting action: {}'.format(error))

        for child in tree:
            # print(tree, child)
            if child:
                self.load_actionable_objects(index + 1, child)
