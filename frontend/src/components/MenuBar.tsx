const MenuBar = ({ items }: { items: string[] }) => {
  return (
    <div className="menu-bar" role="menubar">
      {items.map((item) => (
        <button key={item} role="menuitem" type="button">
          {item}
        </button>
      ))}
    </div>
  );
};

export default MenuBar;
