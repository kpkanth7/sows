export default function CategoryPills({ categories, activeCategory, onSelect }) {
  return (
    <div className="category-pills">
      {categories.map(cat => (
        <button
          key={cat}
          className={`pill ${activeCategory === cat ? 'active' : ''}`}
          onClick={() => onSelect(cat)}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
