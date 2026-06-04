export default function CategoryPills({ categories, activeCategory, onSelect }) {
  return (
    <div className="category-pills" role="tablist" aria-label="News categories">
      {categories.map(cat => (
        <button
          key={cat}
          className={`pill ${activeCategory === cat ? 'active' : ''}`}
          onClick={() => onSelect(cat)}
          role="tab"
          aria-selected={activeCategory === cat}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
