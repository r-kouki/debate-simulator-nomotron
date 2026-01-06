import MenuBar from "../../components/MenuBar";

const HelpWindow = () => {
  return (
    <div>
      <MenuBar items={["File", "View", "Help"]} />
      <h3>Debate Simulator Help</h3>
      <p>Use the Start menu or desktop icons to open features.</p>
      <ul>
        <li>New Debate: configure a match and launch the session.</li>
        <li>Topic Explorer: research topics and add them to your debate.</li>
        <li>Scoreboard: view profile, stats, and achievements.</li>
      </ul>
      <p>Keyboard: Enter sends a turn, Shift+Enter adds a new line.</p>
    </div>
  );
};

export default HelpWindow;
