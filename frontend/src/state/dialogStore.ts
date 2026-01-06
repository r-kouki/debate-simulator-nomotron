import { create } from "zustand";

export type DialogAction = {
  label: string;
  onClick: () => void;
};

export type DialogPayload = {
  id: string;
  title: string;
  message: string;
  actions: DialogAction[];
};

type DialogState = {
  dialogs: DialogPayload[];
  openDialog: (dialog: Omit<DialogPayload, "id">) => void;
  closeDialog: (id: string) => void;
};

const makeId = () => Math.random().toString(36).slice(2, 10);

export const useDialogStore = create<DialogState>((set) => ({
  dialogs: [],
  openDialog: (dialog) =>
    set((state) => ({
      dialogs: [
        ...state.dialogs,
        {
          ...dialog,
          id: makeId()
        }
      ]
    })),
  closeDialog: (id) =>
    set((state) => ({ dialogs: state.dialogs.filter((item) => item.id !== id) }))
}));
