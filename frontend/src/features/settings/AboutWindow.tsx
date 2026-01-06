import MenuBar from "../../components/MenuBar";

const AboutWindow = () => {
  return (
    <div>
      <MenuBar items={["File", "Help"]} />
      <h3>About Debate Simulator</h3>
      <p>Version 0.1.0</p>
      <p>A Windows 98-inspired debate game with AI opponents and live scoring.</p>
    </div>
  );
};

export default AboutWindow;
