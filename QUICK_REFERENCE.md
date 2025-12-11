# Quick Reference Card

## 🚀 Start Development Servers

```bash
# Terminal 1 - Django
source venv/bin/activate
python manage.py runserver

# Terminal 2 - Tailwind (hot reload)
source venv/bin/activate
python manage.py tailwind start
```

**Access:** http://127.0.0.1:8000/calculator/multi-phase/

---

## 🎯 HTMX Request Detection

```python
# In any view
if request.htmx:
    # Return partial HTML
    return render(request, 'partials/content.html', context)
else:
    # Return full page
    return render(request, 'full_page.html', context)
```

---

## 🎨 HTMX Swap with Animations

```html
<form
    hx-post="{% url 'endpoint' %}"
    hx-target="#results"
    hx-swap="innerHTML swap:0.3s settle:0.3s"
    hx-indicator="#loading">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

---

## ⚡ HTMX Attributes Cheat Sheet

```html
hx-get="/url"              - GET request
hx-post="/url"             - POST request
hx-target="#element"       - Where to put response
hx-swap="innerHTML"        - How to swap content
hx-trigger="click"         - When to trigger
hx-indicator="#loading"    - Loading indicator
hx-include="[name='age']"  - Include other inputs
hx-confirm="Are you sure?" - Confirmation dialog
```

---

## 🎭 CSS Animations

**Fade In:**
```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
    animation: fadeIn 0.5s ease-out;
}
```

**HTMX Swap:**
```css
.htmx-swapping { opacity: 0; transition: opacity 0.3s; }
.htmx-settling { opacity: 1; transition: opacity 0.3s; }
```

---

## 🔧 Common Git Commands

```bash
# Check status
git status

# Stage all changes
git add .

# Commit with message
git commit -m "Your message"

# Push to GitHub
git push origin main

# View recent commits
git log --oneline -5
```

---

## 📁 Project Structure

```
calculator/
├── phase_forms.py          # Forms for 4 phases
├── phase_calculator.py     # Calculation logic
├── htmx_views.py          # HTMX endpoints
├── views.py               # Regular views
├── urls.py                # URL routing
└── templates/calculator/
    ├── multi_phase_calculator.html
    └── partials/
        ├── accumulation_results.html
        ├── phased_retirement_results.html
        ├── active_retirement_results.html
        └── late_retirement_results.html
```

---

## 🎨 Tailwind Utility Classes

```html
<!-- Layout -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

<!-- Card -->
<div class="bg-white rounded-xl shadow-lg p-8">

<!-- Button -->
<button class="bg-blue-600 hover:bg-blue-700 text-white
               font-semibold py-3 px-6 rounded-lg
               transition-colors">

<!-- Input -->
<input class="w-full px-4 py-2 border border-gray-300
              rounded-lg focus:ring-2 focus:ring-blue-500">
```

---

## 🐛 Debugging HTMX

**Browser Console:**
```javascript
// Log all HTMX events
document.body.addEventListener('htmx:afterRequest', (e) => {
    console.log('HTMX request:', e.detail);
});
```

**Network Tab:**
- Look for `HX-Request: true` header
- Check response is HTML fragment
- Verify status codes

**Django:**
```python
# Add print statements
print(f"HTMX: {request.htmx}")
print(f"Target: {request.htmx.target if request.htmx else None}")
```

---

## 📚 Documentation Files

- **SUMMARY.md** - Complete project overview
- **DJANGO_HTMX_GUIDE.md** - django-htmx comprehensive guide
- **HTMX_GUIDE.md** - Original HTMX reference
- **TEMPLATE_GUIDE.md** - Django template reference

---

## 🌐 URLs

**Multi-Phase Calculator:**
http://127.0.0.1:8000/calculator/multi-phase/

**Simple Calculator:**
http://127.0.0.1:8000/calculator/

**Admin:**
http://127.0.0.1:8000/admin/

**GitHub Repo:**
https://github.com/marvokdolor/retirement-planner

---

## 🎯 4 Retirement Phases

1. **Accumulation** (Blue) - Building wealth
2. **Phased Retirement** (Purple) - Semi-retirement
3. **Active Retirement** (Orange) - Early retirement
4. **Late Retirement** (Indigo) - Legacy planning

---

## 📦 Dependencies

```
Django==6.0
django-htmx==1.27.0
django-tailwind
python-decouple
```

Install: `pip install -r requirements.txt`

---

## ⚙️ Settings Quick Config

**INSTALLED_APPS:**
```python
'django_htmx',
'tailwind',
'theme',
'calculator',
```

**MIDDLEWARE:**
```python
'django_htmx.middleware.HtmxMiddleware',
```

---

## 🎨 Color Palette

- **Primary:** `blue-600` (#3B82F6)
- **Accent 1:** `purple-600` (#A855F7)
- **Accent 2:** `orange-600` (#F97316)
- **Accent 3:** `indigo-600` (#6366F1)
- **Success:** `green-600` (#16A34A)
- **Warning:** `yellow-600` (#CA8A04)
- **Error:** `red-600` (#DC2626)

---

## 🔐 Environment Variables

**.env:**
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Never commit .env to git!**

---

## 🧪 Testing Checklist

- [ ] Tab switching animations work
- [ ] All 4 phases calculate correctly
- [ ] Loading spinners appear
- [ ] Results fade in smoothly
- [ ] Forms validate properly
- [ ] Error messages display
- [ ] Works without JavaScript (fallback)
- [ ] Mobile responsive

---

## 💡 Tips

1. Always activate venv: `source venv/bin/activate`
2. Use HTMX CDN for simple projects
3. Use django-htmx for production
4. Keep partials simple (fragment only)
5. Always provide fallback for non-HTMX
6. Use `request.htmx` to detect
7. Add CSRF tokens to forms
8. Debounce search inputs
9. Use loading indicators
10. Test on mobile devices

---

**Need Help?** Check the comprehensive guides:
- DJANGO_HTMX_GUIDE.md
- HTMX_GUIDE.md
- SUMMARY.md
