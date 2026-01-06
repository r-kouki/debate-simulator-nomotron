import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../src/app/App";

const openStartMenu = async (user: ReturnType<typeof userEvent.setup>) => {
  const startButton = screen.getByRole("button", { name: /start/i });
  await user.click(startButton);
};

describe("Debate Simulator", () => {
  it("renders the desktop", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /start/i })).toBeInTheDocument();
  });

  it("opens and closes a window from the start menu", async () => {
    render(<App />);
    const user = userEvent.setup();
    await openStartMenu(user);
    const newDebateButton = screen.getByRole("button", { name: /new debate/i });
    await user.click(newDebateButton);
    expect(screen.getByText(/new debate/i)).toBeInTheDocument();
    const closeButtons = screen.getAllByLabelText(/close/i);
    await user.click(closeButtons[0]);
  });
});
