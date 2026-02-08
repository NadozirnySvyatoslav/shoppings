import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_BASE = '/api'
const SAVED_LISTS_KEY = 'shopping_saved_lists'
const THEME_KEY = 'shopping_theme'

function App() {
  const [listId, setListId] = useState(null)
  const [list, setList] = useState(null)
  const [newItemName, setNewItemName] = useState('')
  const [newListName, setNewListName] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [savedLists, setSavedLists] = useState([])
  const [editingId, setEditingId] = useState(null)
  const [editingName, setEditingName] = useState('')
  const [showInfo, setShowInfo] = useState(false)
  const [popularItems, setPopularItems] = useState([])
  const [showPopularHints, setShowPopularHints] = useState(false)
  const [installPrompt, setInstallPrompt] = useState(null)
  const [theme, setTheme] = useState('light')
  const inputRef = useRef(null)
  const editInputRef = useRef(null)
  const hintTimerRef = useRef(null)

  // Load saved lists from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(SAVED_LISTS_KEY)
    if (saved) {
      try {
        setSavedLists(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to parse saved lists')
      }
    }
  }, [])

  // Load and apply theme
  useEffect(() => {
    const savedTheme = localStorage.getItem(THEME_KEY)
    if (savedTheme) {
      setTheme(savedTheme)
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark')
    }
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  // PWA install prompt
  useEffect(() => {
    const handler = (e) => {
      e.preventDefault()
      setInstallPrompt(e)
    }
    window.addEventListener('beforeinstallprompt', handler)

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setInstallPrompt(null)
    }

    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = async () => {
    if (!installPrompt) return

    installPrompt.prompt()
    const { outcome } = await installPrompt.userChoice

    if (outcome === 'accepted') {
      setInstallPrompt(null)
    }
  }

  // Get list ID from URL
  useEffect(() => {
    const path = window.location.pathname
    const id = path.split('/').filter(Boolean)[0]
    if (id) {
      setListId(id)
    } else {
      setLoading(false)
    }
  }, [])

  // Focus edit input when editing starts
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus()
      editInputRef.current.select()
    }
  }, [editingId])

  // Load popular items
  useEffect(() => {
    const loadPopular = async () => {
      try {
        const res = await fetch(`${API_BASE}/popular?limit=50`)
        const data = await res.json()
        setPopularItems(data.map(item => item.name))
      } catch (err) {
        console.error('Failed to load popular items')
      }
    }
    loadPopular()
  }, [])

  // Show hints after 5 seconds if list is empty (once shown, stay visible)
  useEffect(() => {
    if (list && list.items && list.items.length === 0 && !showPopularHints) {
      hintTimerRef.current = setTimeout(() => {
        setShowPopularHints(true)
      }, 5000)
    }

    return () => {
      if (hintTimerRef.current) {
        clearTimeout(hintTimerRef.current)
      }
    }
  }, [list, showPopularHints])

  // Save list to localStorage when loaded
  const saveListToLocal = (listData) => {
    const saved = localStorage.getItem(SAVED_LISTS_KEY)
    let lists = []
    if (saved) {
      try {
        lists = JSON.parse(saved)
      } catch (e) {
        lists = []
      }
    }

    // Remove if already exists
    lists = lists.filter(l => l.id !== listData.id)

    // Get first 3 item names for preview
    const itemsPreview = listData.items
      ? listData.items.slice(0, 3).map(i => i.name)
      : []

    // Add to beginning
    lists.unshift({
      id: listData.id,
      name: listData.name,
      lastVisited: new Date().toISOString(),
      itemsCount: listData.items?.length || 0,
      itemsPreview: itemsPreview
    })

    // Keep only last 20 lists
    lists = lists.slice(0, 20)

    localStorage.setItem(SAVED_LISTS_KEY, JSON.stringify(lists))
    setSavedLists(lists)
  }

  // Load list
  useEffect(() => {
    if (!listId) return

    const loadList = async () => {
      try {
        const res = await fetch(`${API_BASE}/lists/${listId}`)
        if (!res.ok) {
          if (res.status === 404) {
            setError('Список не знайдено')
          } else {
            throw new Error('Failed to load list')
          }
          setLoading(false)
          return
        }
        const data = await res.json()
        setList(data)
        saveListToLocal(data)
        setLoading(false)
      } catch (err) {
        setError('Помилка завантаження списку')
        setLoading(false)
      }
    }

    loadList()
  }, [listId])

  // Reload list helper
  const reloadList = async () => {
    try {
      const res = await fetch(`${API_BASE}/lists/${listId}`)
      if (res.ok) {
        const data = await res.json()
        setList(data)
        saveListToLocal(data)
      }
    } catch (err) {
      console.error('Failed to reload list')
    }
  }

  // Fetch suggestions
  useEffect(() => {
    if (newItemName.length < 2) {
      setSuggestions([])
      return
    }

    const fetchSuggestions = async () => {
      try {
        const res = await fetch(`${API_BASE}/suggestions?q=${encodeURIComponent(newItemName)}`)
        const data = await res.json()
        setSuggestions(data)
      } catch (err) {
        console.error('Failed to fetch suggestions')
      }
    }

    const timer = setTimeout(fetchSuggestions, 150)
    return () => clearTimeout(timer)
  }, [newItemName])

  const createList = async (e) => {
    e.preventDefault()
    if (!newListName.trim()) return

    try {
      const res = await fetch(`${API_BASE}/lists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newListName })
      })
      const data = await res.json()
      window.location.href = `/${data.id}`
    } catch (err) {
      setError('Помилка створення списку')
    }
  }

  const addItem = async (name) => {
    const itemName = name || newItemName
    if (!itemName.trim()) return

    setNewItemName('')
    setSuggestions([])
    setShowSuggestions(false)

    try {
      await fetch(`${API_BASE}/lists/${listId}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: itemName.trim() })
      })
      await reloadList()
      inputRef.current?.focus()
    } catch (err) {
      setError('Помилка додавання товару')
    }
  }

  const toggleItem = async (itemId) => {
    // Optimistic update for instant feedback
    setList(prev => ({
      ...prev,
      items: prev.items.map(i =>
        i.id === itemId ? { ...i, completed: !i.completed } : i
      )
    }))

    try {
      await fetch(`${API_BASE}/lists/${listId}/items/${itemId}`, {
        method: 'PATCH'
      })
    } catch (err) {
      setError('Помилка оновлення товару')
      await reloadList()
    }
  }

  const deleteItem = async (itemId) => {
    // Optimistic update for instant feedback
    setList(prev => ({
      ...prev,
      items: prev.items.filter(i => i.id !== itemId)
    }))

    try {
      await fetch(`${API_BASE}/lists/${listId}/items/${itemId}`, {
        method: 'DELETE'
      })
    } catch (err) {
      setError('Помилка видалення товару')
      await reloadList()
    }
  }

  const startEditing = (item) => {
    setEditingId(item.id)
    setEditingName(item.name)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditingName('')
  }

  const saveEditing = async () => {
    if (!editingName.trim() || !editingId) {
      cancelEditing()
      return
    }

    const newName = editingName.trim()
    const itemId = editingId

    // Optimistic update for instant feedback
    setList(prev => ({
      ...prev,
      items: prev.items.map(i =>
        i.id === itemId ? { ...i, name: newName } : i
      )
    }))
    cancelEditing()

    try {
      await fetch(`${API_BASE}/lists/${listId}/items/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      })
    } catch (err) {
      setError('Помилка редагування товару')
      await reloadList()
    }
  }

  const handleEditKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      saveEditing()
    } else if (e.key === 'Escape') {
      cancelEditing()
    }
  }

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href)
    alert('Посилання скопійовано!')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addItem()
    }
  }

  const selectSuggestion = (suggestion) => {
    addItem(suggestion)
  }

  const removeFromSaved = (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    const updated = savedLists.filter(l => l.id !== id)
    localStorage.setItem(SAVED_LISTS_KEY, JSON.stringify(updated))
    setSavedLists(updated)
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date

    if (diff < 60000) return 'щойно'
    if (diff < 3600000) return `${Math.floor(diff / 60000)} хв тому`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} год тому`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} дн тому`

    return date.toLocaleDateString('uk-UA')
  }

  const renderItem = (item, isCompleted) => {
    const isEditing = editingId === item.id

    return (
      <div key={item.id} className={`item ${isCompleted ? 'completed' : ''}`}>
        <label className="item-label">
          <input
            type="checkbox"
            checked={isCompleted}
            onChange={() => toggleItem(item.id)}
          />
          <span className="checkmark"></span>
          {isEditing ? (
            <input
              ref={editInputRef}
              type="text"
              value={editingName}
              onChange={(e) => setEditingName(e.target.value)}
              onKeyDown={handleEditKeyDown}
              onBlur={saveEditing}
              className="edit-input"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span
              className="item-name"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                startEditing(item)
              }}
            >
              {item.name}
            </span>
          )}
        </label>
        {isEditing ? (
          <button
            onClick={saveEditing}
            className="btn-save"
            aria-label="Зберегти"
          >
            ✓
          </button>
        ) : (
          <button
            onClick={() => deleteItem(item.id)}
            className="btn-delete"
            aria-label="Видалити"
          >
            ×
          </button>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Завантаження...</div>
      </div>
    )
  }

  if (error && !list) {
    return (
      <div className="container">
        <div className="error">{error}</div>
        <a href="/" className="btn btn-primary">На головну</a>
      </div>
    )
  }

  // Info modal
  const InfoModal = () => (
    <div className="modal-overlay" onClick={() => setShowInfo(false)}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={() => setShowInfo(false)}>×</button>
        <h2>Як користуватися</h2>

        <div className="info-section">
          <h3>Створення списку</h3>
          <p>Введіть назву та натисніть "Створити список"</p>
        </div>

        <div className="info-section">
          <h3>Спільний доступ</h3>
          <p>Натисніть "Поділитися" і надішліть посилання. Всі зміни синхронізуються в реальному часі!</p>
        </div>

        <div className="info-section">
          <h3>Підказки</h3>
          <p>Почніть вводити назву товару - з'являться підказки</p>
        </div>

        <div className="info-section">
          <h3>Редагування</h3>
          <p>Натисніть на назву товару щоб змінити її</p>
        </div>

        <div className="info-warning">
          <h3>Важливо</h3>
          <ul>
            <li>Реєстрація не потрібна - все анонімно</li>
            <li>Будь-хто з посиланням може редагувати список</li>
            <li>Списки зберігаються локально у браузері</li>
          </ul>
        </div>

        <div className="info-disclaimer">
          <p><strong>Використовуйте на свій страх і ризик.</strong></p>
          <p>Сервіс надається "як є" без гарантій. Не зберігайте конфіденційну інформацію.</p>
        </div>
      </div>
    </div>
  )

  // Home page - create new list and show saved
  if (!listId) {
    return (
      <div className="container">
        <div className="home-header">
          <h1>Список покупок</h1>
          <div className="header-buttons">
            {installPrompt && (
              <button className="btn-logo" onClick={handleInstall} aria-label="Встановити додаток">
                <img src="/logo.png" alt="Встановити" className="logo-small" />
              </button>
            )}
            <button className="btn-theme" onClick={toggleTheme} aria-label="Змінити тему">
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <button className="btn-info" onClick={() => setShowInfo(true)} aria-label="Інформація">?</button>
          </div>
        </div>
        <p className="subtitle">Створіть список і поділіться з іншими</p>

        {showInfo && <InfoModal />}

        <form onSubmit={createList} className="create-form">
          <input
            type="text"
            value={newListName}
            onChange={(e) => setNewListName(e.target.value)}
            placeholder="Назва списку"
            className="input"
            autoFocus
          />
          <button type="submit" className="btn btn-primary">
            Створити список
          </button>
        </form>

        {savedLists.length > 0 && (
          <div className="saved-lists">
            <h2>Мої списки</h2>
            <div className="saved-lists-grid">
              {savedLists.map(item => (
                <a key={item.id} href={`/${item.id}`} className="saved-list-card">
                  <div className="saved-list-header">
                    <div className="saved-list-name">{item.name}</div>
                    {item.itemsCount > 0 && (
                      <span className="saved-list-count">{item.itemsCount}</span>
                    )}
                  </div>
                  {item.itemsPreview && item.itemsPreview.length > 0 && (
                    <div className="saved-list-preview">
                      {item.itemsPreview.join(', ')}
                      {item.itemsCount > 3 && '...'}
                    </div>
                  )}
                  <div className="saved-list-date">{formatDate(item.lastVisited)}</div>
                  <button
                    className="saved-list-remove"
                    onClick={(e) => removeFromSaved(e, item.id)}
                    aria-label="Видалити зі збережених"
                  >
                    ×
                  </button>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // List page
  const pendingItems = list?.items?.filter(i => !i.completed) || []
  const completedItems = list?.items?.filter(i => i.completed) || []
  const progress = list?.items?.length
    ? Math.round((completedItems.length / list.items.length) * 100)
    : 0

  return (
    <div className="container">
      <header className="header">
        <div className="header-left">
          <a href="/" className="back-btn" aria-label="На головну">←</a>
          <div className="header-title">
            <h1>{list?.name || 'Список покупок'}</h1>
            {list?.items?.length > 0 && (
              <span className="list-count">{list.items.length} товарів</span>
            )}
          </div>
        </div>
        <div className="header-buttons">
          <button className="btn-theme" onClick={toggleTheme} aria-label="Змінити тему">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <button onClick={copyLink} className="btn btn-secondary">
            Поділитися
          </button>
        </div>
      </header>

      {list?.items?.length > 0 && (
        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span className="progress-text">
            {completedItems.length} / {list.items.length} куплено
          </span>
        </div>
      )}

      <div className="add-item-container">
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={newItemName}
            onChange={(e) => {
              setNewItemName(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            onKeyDown={handleKeyDown}
            placeholder="Додати товар..."
            className="input"
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul className="suggestions">
              {suggestions.map((s, i) => (
                <li key={i} onMouseDown={() => selectSuggestion(s)}>
                  {s}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button onClick={() => addItem()} className="btn btn-primary btn-add">
          +
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="items-list">
        {pendingItems.map(item => renderItem(item, false))}

        {completedItems.length > 0 && (
          <>
            <div className="divider">Куплено</div>
            {completedItems.map(item => renderItem(item, true))}
          </>
        )}

        {list?.items?.length === 0 && (
          <div className="empty">
            Список порожній. Додайте перший товар!
          </div>
        )}
      </div>

      {showPopularHints && popularItems.length > 0 && (
        <div className="popular-hints">
          <h3>Популярні товари</h3>
          <div className="popular-grid">
            {popularItems.slice(0, 50).map((item, i) => (
              <button
                key={i}
                className="popular-item"
                onClick={() => addItem(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
