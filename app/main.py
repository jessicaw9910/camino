"""
Camino Audio Guide - Multi-Tour GPS App

A GPS-triggered audio guide app supporting multiple tours.
Each tour is a subdirectory in data/ containing a scripts.json file.

Features:
- Tour selection landing page with cover images
- Interactive map showing all POIs for selected tour
- GPS tracking with automatic audio playback when near a POI
- Manual audio playback for any POI
- Distance-based trigger system (configurable radius)

Requirements:
    pip install kivy kivy-garden.mapview plyer
"""

import json
import re
import webbrowser
from pathlib import Path
from functools import partial

import pygame  # For reliable audio with seek support

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.properties import (
    NumericProperty, StringProperty, BooleanProperty, 
    ListProperty, ObjectProperty
)
from kivy.utils import platform

# Conditional imports for mobile
GPS_AVAILABLE = False
gps = None
if platform in ('android', 'ios'):
    try:
        from plyer import gps
        GPS_AVAILABLE = True
    except Exception:
        pass
if not GPS_AVAILABLE:
    print("GPS not available - running in simulation mode")

try:
    from kivy_garden.mapview import MapView, MapMarker, MapMarkerPopup
    from kivy_garden.mapview.source import MapSource
    MAPVIEW_AVAILABLE = True
except ImportError:
    MAPVIEW_AVAILABLE = False
    MapSource = None
    print("MapView not available - install with: pip install kivy-garden.mapview")

from kivy.lang import Builder

# KV Language UI Definition
KV = '''
#:import MapView kivy_garden.mapview.MapView

<TourCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: 220
    padding: 10
    spacing: 5
    canvas.before:
        Color:
            rgba: 0.2, 0.2, 0.25, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
    
    AsyncImage:
        source: root.cover_image
        size_hint_y: 0.7
        allow_stretch: True
        keep_ratio: True
    
    Label:
        text: root.tour_name
        font_size: '16sp'
        bold: True
        size_hint_y: 0.15
        text_size: self.size
        halign: 'center'
        valign: 'middle'
    
    Label:
        text: root.tour_description
        font_size: '12sp'
        color: 0.7, 0.7, 0.7, 1
        size_hint_y: 0.15
        text_size: self.size
        halign: 'center'
        valign: 'middle'


<TourSelectScreen>:
    BoxLayout:
        orientation: 'vertical'
        
        BoxLayout:
            size_hint_y: 0.12
            padding: 15
            canvas.before:
                Color:
                    rgba: 0.15, 0.15, 0.2, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Label:
                text: 'Camino Audio Guides'
                font_size: '22sp'
                bold: True
        
        ScrollView:
            size_hint_y: 0.88
            
            BoxLayout:
                id: tour_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 15
                padding: 15


<TourScreen>:
    tour_id: ''
    
    FloatLayout:
        id: main_float
        
        # Main content layer
        BoxLayout:
            orientation: 'vertical'
            pos_hint: {'x': 0, 'y': 0}
            size_hint: 1, 1
            
            BoxLayout:
                size_hint_y: 0.08
                padding: 10
                spacing: 10
                canvas.before:
                    Color:
                        rgba: 0.2, 0.2, 0.3, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                Button:
                    text: '< Tours'
                    size_hint_x: 0.2
                    on_release: root.go_back()
                
                Label:
                    id: tour_title
                    text: 'Tour'
                    font_size: '16sp'
                    bold: True
                    size_hint_x: 0.35
                
                ToggleButton:
                    id: gps_toggle
                    text: 'GPS: OFF' if self.state == 'normal' else 'GPS: ON'
                    size_hint_x: 0.22
                    on_state: root.toggle_gps(self.state)
                    background_color: (0.2, 0.6, 0.2, 1) if self.state == 'down' else (0.5, 0.2, 0.2, 1)
                
                Button:
                    text: 'List'
                    size_hint_x: 0.23
                    on_release: root.show_poi_list()
            
            BoxLayout:
                id: map_container
                size_hint_y: 0.69
                
                MapViewWidget:
                    id: map_widget
                
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_x: None
                    width: 50
                    padding: 5
                    spacing: 5
                    
                    Widget:
                        size_hint_y: 0.5
                    
                    Button:
                        text: '+'
                        font_size: '20sp'
                        size_hint_y: None
                        height: 45
                        on_release: root.ids.map_widget.zoom_in()
                    
                    Button:
                        text: '-'
                        font_size: '20sp'
                        size_hint_y: None
                        height: 45
                        on_release: root.ids.map_widget.zoom_out()
                    
                    Widget:
                        size_hint_y: 0.5
            
            BoxLayout:
                id: info_panel
                size_hint_y: 0.18
                padding: 10
                spacing: 10
                canvas.before:
                    Color:
                        rgba: 0.15, 0.15, 0.2, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_x: 0.55
                    spacing: 5
                    
                    Label:
                        id: current_poi_label
                        text: 'Select a point of interest'
                        font_size: '14sp'
                        text_size: self.width, None
                        size_hint_y: 0.4
                        halign: 'left'
                        valign: 'middle'
                        markup: True
                    
                    BoxLayout:
                        size_hint_y: 0.6
                        spacing: 8
                        
                        Label:
                            id: time_label
                            text: '0:00'
                            size_hint_x: None
                            width: 40
                            font_size: '11sp'
                        
                        Slider:
                            id: progress_slider
                            min: 0
                            max: 100
                            value: 0
                            size_hint_x: 1
                            on_touch_up: root.seek_audio(self.value) if self.collide_point(*args[1].pos) else None
                        
                        Label:
                            id: duration_label
                            text: '0:00'
                            size_hint_x: None
                            width: 40
                            font_size: '11sp'
                
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_x: 0.45
                    spacing: 5
                    
                    BoxLayout:
                        spacing: 5
                        
                        Button:
                            id: play_btn
                            text: 'Play'
                            on_release: root.toggle_playback()
                            disabled: True
                        
                        Button:
                            id: stop_btn
                            text: 'Stop'
                            on_release: root.stop_audio()
                            disabled: True
                    
                    ToggleButton:
                        id: text_toggle
                        text: 'Show Text'
                        state: 'normal'
                        on_state: root.toggle_text_panel(self.state)
                        disabled: True
            
            BoxLayout:
                size_hint_y: 0.05
                padding: [10, 2]
                canvas.before:
                    Color:
                        rgba: 0.1, 0.1, 0.15, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                
                Label:
                    text: 'Trigger radius:'
                    size_hint_x: 0.3
                    font_size: '12sp'
                
                Slider:
                    id: radius_slider
                    min: 50
                    max: 500
                    value: 150
                    size_hint_x: 0.5
                    on_value: root.update_radius(self.value)
                
                Label:
                    id: radius_label
                    text: '150m'
                    size_hint_x: 0.2
                    font_size: '12sp'
        
        # Text panel overlay (slides up above bottom controls)
        ScrollView:
            id: text_panel
            pos_hint: {'x': 0, 'y': -0.46}
            size_hint: 1, 0.46
            opacity: 0
            disabled: True
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.15, 0.98
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Label:
                id: poi_text_label
                text: ''
                font_size: '14sp'
                color: 1, 1, 1, 1
                text_size: self.width - 30, None
                size_hint_y: None
                height: max(self.texture_size[1] + 40, self.parent.height)
                halign: 'left'
                valign: 'top'
                padding: [15, 15]
                markup: True


<MapViewWidget>:
    # Custom MapView container


<POIListPopup>:
    title: 'Points of Interest'
    size_hint: 0.9, 0.9
    
    BoxLayout:
        orientation: 'vertical'
        
        ScrollView:
            id: scroll_view
            
            BoxLayout:
                id: poi_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 5
                padding: 10
        
        Button:
            text: 'Close'
            size_hint_y: 0.1
            on_release: root.dismiss()
'''


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two GPS coordinates in meters."""
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000
    return c * r


def get_data_dir():
    """Get the data directory path based on platform."""
    possible_paths = [
        Path(__file__).parent.parent / 'data',
        Path(__file__).parent / 'data',
        Path.home() / 'camino' / 'data',
    ]
    
    if platform == 'android':
        try:
            # Kivy App's user_data_dir for bundled assets
            from kivy.app import App
            app = App.get_running_app()
            if app:
                possible_paths.insert(0, Path(app.user_data_dir) / 'data')
        except Exception:
            pass
        try:
            from android.storage import app_storage_path
            possible_paths.insert(0, Path(app_storage_path()) / 'data')
        except ImportError:
            pass
        # Android external storage fallback
        possible_paths.append(Path('/storage/emulated/0/Download/camino/data'))
        possible_paths.append(Path('/sdcard/camino/data'))
    
    for path in possible_paths:
        if path.exists():
            print(f"[DATA] Using data directory: {path}")
            return path
    
    # Default fallback
    print(f"[DATA] No data dir found, using fallback")
    return Path(__file__).parent.parent / 'data'


def discover_tours(data_dir: Path) -> list:
    """Discover available tours in the data directory."""
    tours = []
    
    if not data_dir.exists():
        return tours
    
    for subdir in data_dir.iterdir():
        if subdir.is_dir():
            scripts_file = subdir / 'scripts.json'
            if scripts_file.exists():
                # Load tour metadata
                try:
                    with open(scripts_file, 'r', encoding='utf-8') as f:
                        pois = json.load(f)
                    
                    # Try to load tour config if exists
                    config_file = subdir / 'tour.json'
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    else:
                        config = {}
                    
                    # Generate display name from directory name
                    display_name = config.get('name', subdir.name.replace('_', ' ').title())
                    
                    # Find cover image
                    cover_image = ''
                    for ext in ['jpg', 'jpeg', 'png', 'webp']:
                        cover = subdir / f'cover.{ext}'
                        if cover.exists():
                            cover_image = str(cover)
                            break
                    
                    # Calculate center point from POIs
                    if pois:
                        avg_lat = sum(p['lat'] for p in pois) / len(pois)
                        avg_lon = sum(p['lon'] for p in pois) / len(pois)
                    else:
                        avg_lat, avg_lon = 0, 0
                    
                    tours.append({
                        'id': subdir.name,
                        'name': display_name,
                        'description': config.get('description', f'{len(pois)} points of interest'),
                        'cover_image': cover_image,
                        'path': subdir,
                        'poi_count': len(pois),
                        'center_lat': avg_lat,
                        'center_lon': avg_lon,
                    })
                except Exception as e:
                    print(f"Error loading tour from {subdir}: {e}")
    
    return tours


class TourCard(BoxLayout):
    """A card widget displaying tour info."""
    tour_id = StringProperty('')
    tour_name = StringProperty('')
    tour_description = StringProperty('')
    cover_image = StringProperty('')


class TourSelectScreen(Screen):
    """Landing page showing available tours."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tours = []
        Clock.schedule_once(self.load_tours, 0.1)
    
    def load_tours(self, dt):
        """Discover and display available tours."""
        data_dir = get_data_dir()
        self.tours = discover_tours(data_dir)
        
        tour_list = self.ids.tour_list
        tour_list.clear_widgets()
        
        if not self.tours:
            tour_list.add_widget(Label(
                text='No tours found.\n\nAdd tour directories to data/ with scripts.json files.',
                font_size='16sp',
                halign='center',
                size_hint_y=None,
                height=200
            ))
            return
        
        for tour in self.tours:
            card = TourCard(
                tour_id=tour['id'],
                tour_name=tour['name'],
                tour_description=tour['description'],
                cover_image=tour['cover_image'] if tour['cover_image'] else '',
            )
            card.bind(on_touch_up=partial(self.on_tour_selected, tour))
            tour_list.add_widget(card)
    
    def on_tour_selected(self, tour, widget, touch):
        """Handle tour card tap."""
        if widget.collide_point(*touch.pos):
            app = App.get_running_app()
            app.open_tour(tour)


class UserLocationMarker(MapMarker):
    """Custom marker for user's GPS location - blue circle with white border."""
    
    def __init__(self, **kwargs):
        # Use an empty/transparent source so we can draw custom graphics
        kwargs['source'] = ''
        super().__init__(**kwargs)
        self.size = (24, 24)
        self.anchor_x = 0.5
        self.anchor_y = 0.5
        self._draw_marker()
        self.bind(pos=self._draw_marker, size=self._draw_marker)
    
    def _draw_marker(self, *args):
        """Draw a blue circle with white border."""
        from kivy.graphics import Color, Ellipse, Line
        self.canvas.clear()
        with self.canvas:
            # White outer ring
            Color(1, 1, 1, 1)
            Ellipse(pos=(self.x + 2, self.y + 2), size=(20, 20))
            # Blue fill
            Color(0.2, 0.5, 1, 1)  # Bright blue
            Ellipse(pos=(self.x + 4, self.y + 4), size=(16, 16))
            # White center dot
            Color(1, 1, 1, 1)
            Ellipse(pos=(self.x + 9, self.y + 9), size=(6, 6))


class MapViewWidget(BoxLayout):
    """Container for MapView with POI markers."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.map_view = None
        self.markers = []
        self.user_marker = None
        self.current_open_marker = None
        self.on_map_touch_callback = None
    
    def setup_map(self, center_lat=32.5, center_lon=-106.5):
        """Initialize the map view."""
        self.clear_widgets()
        self.markers = []
        
        if not MAPVIEW_AVAILABLE:
            self.add_widget(Label(
                text='MapView not available.\nInstall: pip install kivy-garden.mapview',
                halign='center'
            ))
            return
        
        # CartoDB Positron - clean light style
        cartodb_source = MapSource(
            url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
            cache_key="cartodb_positron",
            min_zoom=0,
            max_zoom=19,
            attribution="© OpenStreetMap contributors, © CARTO"
        )
        self.map_view = MapView(
            zoom=8,
            lat=center_lat,
            lon=center_lon,
            map_source=cartodb_source
        )
        # Enable scroll wheel zoom
        self.map_view.bind(on_touch_down=self._handle_scroll)
        self.add_widget(self.map_view)
    
    def _handle_scroll(self, widget, touch):
        """Handle mouse scroll wheel for zooming."""
        if not self.map_view.collide_point(*touch.pos):
            return False
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                self.zoom_out()
                return True
            elif touch.button == 'scrollup':
                self.zoom_in()
                return True
        return False
    
    def add_poi_markers(self, pois, on_marker_click, on_map_touch=None):
        """Add markers for all POIs to the map."""
        if not self.map_view:
            return
        
        # Store callback for map touch (to clear selection)
        self.on_map_touch_callback = on_map_touch
        self.on_marker_click_callback = on_marker_click
        if on_map_touch and self.map_view:
            self.map_view.bind(on_touch_up=self._handle_map_touch)
        
        for poi in pois:
            marker = MapMarkerPopup(
                lat=poi['lat'],
                lon=poi['lon']
            )
            # Store POI reference on marker
            marker.poi = poi
            
            # Create popup label (just shows name, no click needed)
            label = Label(
                text=f"{poi['num']}: {poi['name']}",
                size_hint=(None, None),
                size=(300, 60),
                font_size='12sp',
                text_size=(290, None),
                halign='center',
                valign='middle',
                color=(1, 1, 1, 1)
            )
            # Add dark background to label
            with label.canvas.before:
                label._bg_color = Color(0.2, 0.2, 0.25, 0.95)
                label._bg_rect = Rectangle(pos=label.pos, size=label.size)
            label.bind(pos=self._update_label_rect, size=self._update_label_rect)
            
            marker.add_widget(label)
            
            # Bind to marker press to trigger selection immediately
            marker.bind(on_release=self._on_marker_pressed)
            
            self.map_view.add_marker(marker)
            self.markers.append(marker)
    
    def _update_label_rect(self, instance, value):
        """Update label background rectangle."""
        if hasattr(instance, '_bg_rect'):
            instance._bg_rect.pos = instance.pos
            instance._bg_rect.size = instance.size
    
    def _on_marker_pressed(self, marker):
        """Handle marker being pressed - select the POI."""
        if hasattr(marker, 'poi') and hasattr(self, 'on_marker_click_callback'):
            # Close other popups
            self.close_other_popups(marker)
            self.current_open_marker = marker
            # Call the selection callback
            self.on_marker_click_callback(marker.poi, marker, None)
    
    def clear_markers(self):
        """Remove all POI markers."""
        if self.map_view:
            for marker in self.markers:
                self.map_view.remove_marker(marker)
        self.markers = []
    
    def update_user_location(self, lat, lon):
        """Update the user's location marker on the map."""
        if not self.map_view:
            return
        
        if self.user_marker:
            self.map_view.remove_marker(self.user_marker)
        
        self.user_marker = UserLocationMarker(lat=lat, lon=lon)
        self.map_view.add_marker(self.user_marker)
    
    def center_on_location(self, lat, lon, zoom=12):
        """Center the map on a specific location."""
        if self.map_view:
            self.map_view.center_on(lat, lon)
            self.map_view.zoom = zoom
    
    def zoom_in(self):
        """Increase map zoom level."""
        if self.map_view and self.map_view.zoom < 19:
            self.map_view.zoom += 1
    
    def zoom_out(self):
        """Decrease map zoom level."""
        if self.map_view and self.map_view.zoom > 1:
            self.map_view.zoom -= 1
    
    def close_all_popups(self):
        """Close all marker popups by simulating touch elsewhere."""
        if hasattr(self, 'current_open_marker') and self.current_open_marker:
            self.current_open_marker.is_open = False
            self.current_open_marker = None
        # Also iterate through all markers
        for marker in self.markers:
            marker.is_open = False
    
    def close_other_popups(self, except_marker):
        """Close all marker popups except the specified one."""
        if hasattr(self, 'current_open_marker') and self.current_open_marker:
            if self.current_open_marker != except_marker:
                self.current_open_marker.is_open = False
        for marker in self.markers:
            if marker != except_marker:
                marker.is_open = False
    
    def _handle_map_touch(self, widget, touch):
        """Handle touch on map to potentially clear selection.
        Only clear on simple taps, not on zoom/pan gestures."""
        if not self.map_view.collide_point(*touch.pos):
            return
        
        # Ignore multi-touch (pinch zoom)
        if 'multitouch_sim' in str(touch.device) or touch.is_double_tap:
            return
        
        # Check if this is a move/scroll gesture (not a tap)
        # touch.time_end - touch.time_start > 0.3 means it was held/dragged
        if hasattr(touch, 'time_start') and hasattr(touch, 'time_end'):
            if touch.time_end - touch.time_start > 0.25:
                return  # This was a drag/pan, not a tap
        
        # Check if touch moved significantly (indicates scroll/pan)
        if hasattr(touch, 'ox') and hasattr(touch, 'oy'):
            dx = abs(touch.x - touch.ox)
            dy = abs(touch.y - touch.oy)
            if dx > 10 or dy > 10:
                return  # Touch moved too much - this was a gesture, not a tap
        
        # Check if touch is within the text panel overlay (don't clear if so)
        tour_screen = App.get_running_app().root.get_screen('tour')
        text_panel = tour_screen.ids.text_panel
        if not text_panel.disabled and text_panel.collide_point(*touch.pos):
            return  # Don't clear - user is interacting with text panel
        # Check if touch is on a marker (don't clear if so)
        for marker in self.markers:
            if marker.collide_point(*touch.pos):
                return  # Don't clear - user tapped a marker
        # Touch was a simple tap on map background, clear selection
        if self.on_map_touch_callback:
            self.on_map_touch_callback()


class POIListPopup(Popup):
    """Popup showing a scrollable list of all POIs."""
    pass


class TourScreen(Screen):
    """Screen displaying a specific tour with map and audio controls."""
    
    tour_id = StringProperty('')
    current_poi = ObjectProperty(None, allownone=True)
    gps_enabled = BooleanProperty(False)
    trigger_radius = NumericProperty(150)
    user_lat = NumericProperty(0)
    user_lon = NumericProperty(0)
    played_pois = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pois = []
        self.audio_dir = None
        self.tour_data = None
        self.seek_offset = 0  # Position where current playback started from
        self.is_paused = False
        self.audio_length = 0  # Track audio duration
        self.current_audio_file = None
        self.citation_urls = {}  # Map citation numbers to URLs
        # Initialize pygame mixer
        pygame.mixer.init()
    
    def load_tour(self, tour):
        """Load a specific tour."""
        self.tour_data = tour
        self.tour_id = tour['id']
        self.pois = []
        self.played_pois = []
        
        # Load POI data - always use scripts.json for body/sources
        scripts_file = tour['path'] / 'scripts.json'
        manifest_file = tour['path'] / 'audio' / 'manifest.json'
        
        # Load scripts.json for full POI data (body, sources, etc.)
        if scripts_file.exists():
            with open(scripts_file, 'r', encoding='utf-8') as f:
                raw_pois = json.load(f)
            # Build POI list with full data
            self.pois = []
            for poi in raw_pois:
                self.pois.append({
                    'num': poi['num'],
                    'name': poi['name'],
                    'lat': poi['lat'],
                    'lon': poi['lon'],
                    'audio_file': f"{poi['num']:02d}.mp3",
                    'leg': poi.get('leg', ''),
                    'duration': poi.get('duration', ''),
                    'body': poi.get('body', []),
                    'sources': poi.get('sources', [])
                })
            self.audio_dir = tour['path'] / 'audio'
        elif manifest_file.exists():
            # Fallback to manifest if no scripts.json
            with open(manifest_file, 'r', encoding='utf-8') as f:
                self.pois = json.load(f)
            self.audio_dir = tour['path'] / 'audio'
        
        # Update UI
        Clock.schedule_once(self.setup_tour_ui, 0.1)
    
    def setup_tour_ui(self, dt):
        """Set up the tour UI after loading."""
        self.ids.tour_title.text = self.tour_data['name'][:20]
        
        # Set up map
        self.ids.map_widget.setup_map(
            center_lat=self.tour_data.get('center_lat', 32.5),
            center_lon=self.tour_data.get('center_lon', -106.5)
        )
        self.ids.map_widget.add_poi_markers(
            self.pois, 
            self.on_marker_click,
            on_map_touch=self.clear_selection
        )
        
        # Reset controls
        self.ids.current_poi_label.text = 'Select a point of interest'
        self.ids.play_btn.disabled = True
        self.ids.stop_btn.disabled = True
        self.ids.text_toggle.disabled = True
        self.ids.progress_slider.value = 0
        self.ids.time_label.text = '0:00'
        self.ids.duration_label.text = '0:00'
        # Hide text panel off-screen
        self.ids.text_panel.pos_hint = {'x': 0, 'y': -0.46}
        self.ids.text_panel.opacity = 0
        self.ids.text_panel.disabled = True
        self.ids.text_toggle.state = 'normal'
        # Bind citation clicks
        self.ids.poi_text_label.bind(on_ref_press=self.on_citation_click)
    
    def go_back(self):
        """Return to tour selection."""
        self.stop_audio()
        self.stop_gps()
        app = App.get_running_app()
        app.show_tour_select()
    
    def on_marker_click(self, poi, marker, button):
        """Handle marker click - select the POI."""
        # Just select the POI - popup management is handled by MapViewWidget
        self.select_poi(poi)
    
    def clear_selection(self):
        """Clear the current POI selection."""
        # Stop any playing audio
        Clock.unschedule(self._update_progress)
        pygame.mixer.music.stop()
        self.seek_offset = 0
        self.is_paused = False
        self.current_audio_file = None
        # Close all marker popups
        self.ids.map_widget.close_all_popups()
        self.current_poi = None
        self.ids.current_poi_label.text = 'Select a point of interest'
        self.ids.play_btn.disabled = True
        self.ids.stop_btn.disabled = True
        self.ids.play_btn.text = 'Play'
        self.ids.text_toggle.disabled = True
        self.ids.text_toggle.state = 'normal'
        self.ids.progress_slider.value = 0
        self.ids.progress_slider.max = 100
        self.ids.time_label.text = '0:00'
        self.ids.duration_label.text = '0:00'
        # Hide text panel (slide off-screen)
        self.ids.text_panel.pos_hint = {'x': 0, 'y': -0.46}
        self.ids.text_panel.opacity = 0
        self.ids.text_panel.disabled = True
        self.ids.poi_text_label.text = ''

    def select_poi(self, poi):
        """Select a POI and enable playback."""
        print(f"[DEBUG] POI keys: {poi.keys()}")
        print(f"[DEBUG] POI body exists: {'body' in poi}")
        # Stop any playing audio first
        Clock.unschedule(self._update_progress)
        pygame.mixer.music.stop()
        
        self.seek_offset = 0
        self.is_paused = False
        self.current_audio_file = None
        self.current_poi = poi
        self.ids.current_poi_label.text = f"[b]{poi['num']}: {poi['name']}[/b]"
        self.ids.play_btn.disabled = False
        self.ids.play_btn.text = 'Play'
        self.ids.stop_btn.disabled = False
        self.ids.text_toggle.disabled = False
        self.ids.progress_slider.value = 0
        self.ids.time_label.text = '0:00'
        self.ids.duration_label.text = '0:00'
        # Update text panel content with formatted body and citations
        formatted_text = self.format_poi_text(poi)
        print(f"[DEBUG] Setting text panel: {len(formatted_text)} chars")
        print(f"[DEBUG] First 200 chars: {formatted_text[:200]}")
        self.ids.poi_text_label.text = formatted_text
        # Reset scroll to top
        self.ids.text_panel.scroll_y = 1
        # Automatically show text panel (slide up from bottom)
        self.toggle_text_panel('down')
        self.ids.text_toggle.state = 'down'
    
    def format_poi_text(self, poi):
        """Format POI body text with citations."""
        body = poi.get('body', [])
        sources = poi.get('sources', [])
        
        # Build URL map for in-text citations
        self.citation_urls = {}
        for src in sources:
            n = src.get('n', '')
            url = src.get('url', '')
            if n and url:
                self.citation_urls[str(n)] = url
        
        # Add bold title
        title = f"[b]{poi['num']}. {poi['name']}[/b]\n\n"
        
        # Handle body as list or string
        if isinstance(body, list):
            text_parts = body
        else:
            text_parts = [body] if body else ['No description available.']
        
        # Join paragraphs and convert in-text citations to clickable refs
        body_text = '\n\n'.join(text_parts)
        # Replace [1], [2], etc. with clickable refs
        def replace_citation(match):
            n = match.group(1)
            if n in self.citation_urls:
                return f'[color=6699ff][ref=cite_{n}][{n}][/ref][/color]'
            return match.group(0)
        body_text = re.sub(r'\[(\d+)\]', replace_citation, body_text)
        
        formatted = title + body_text
        
        # Add citations section if sources exist
        if sources:
            formatted += '\n\n' + '-' * 40 + '\n'
            formatted += '[b]Sources:[/b]\n\n'
            for src in sources:
                n = src.get('n', '')
                text = src.get('text', '')
                url = src.get('url', '')
                if n:
                    if url:
                        formatted += f'[color=6699ff][ref={url}][{n}] {text}[/ref][/color]\n\n'
                    else:
                        formatted += f'[{n}] {text}\n\n'
        
        return formatted
    
    def toggle_text_panel(self, state):
        """Toggle the text panel - slides up above bottom controls."""
        panel = self.ids.text_panel
        Animation.cancel_all(panel)
        
        if state == 'down':
            # Slide up to sit above bottom controls (23% from bottom)
            panel.disabled = False
            anim = Animation(pos_hint={'x': 0, 'y': 0.23}, opacity=1, duration=0.25, t='out_cubic')
            anim.start(panel)
            self.ids.text_toggle.text = 'Hide Text'
        else:
            # Slide down off screen
            anim = Animation(pos_hint={'x': 0, 'y': -0.46}, opacity=0, duration=0.2, t='in_cubic')
            anim.bind(on_complete=lambda *_: setattr(panel, 'disabled', True))
            anim.start(panel)
            self.ids.text_toggle.text = 'Show Text'
    
    def on_citation_click(self, instance, ref):
        """Handle citation link clicks."""
        if ref.startswith('cite_'):
            # In-text citation - get URL from citation map
            n = ref.replace('cite_', '')
            url = getattr(self, 'citation_urls', {}).get(n, '')
            if url:
                webbrowser.open(url)
        elif ref.startswith('http'):
            # Direct URL from sources section
            webbrowser.open(ref)

    def toggle_playback(self):
        """Toggle audio playback for the current POI."""
        if pygame.mixer.music.get_busy():
            # Currently playing - pause
            # Calculate full position: offset + elapsed time
            elapsed = pygame.mixer.music.get_pos() / 1000.0
            self.seek_offset = self.seek_offset + elapsed
            print(f"[PAUSE] Saving position: {self.seek_offset:.2f}")
            pygame.mixer.music.pause()
            self.is_paused = True
            Clock.unschedule(self._update_progress)
            self.ids.play_btn.text = 'Play'
        elif self.is_paused and self.current_audio_file:
            # Resume from paused position
            print(f"[RESUME] Resuming from: {self.seek_offset:.2f}")
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.ids.play_btn.text = 'Pause'
            self._start_progress_update()
        else:
            self.play_audio()
    
    def play_audio(self, poi=None):
        """Play audio for the specified or current POI."""
        if poi:
            self.current_poi = poi
        
        if not self.current_poi:
            return
        
        # Stop any existing audio
        Clock.unschedule(self._update_progress)
        pygame.mixer.music.stop()
        
        self.seek_offset = 0
        self.is_paused = False
        
        if not self.audio_dir:
            self.ids.current_poi_label.text = "Audio not generated for this tour"
            return
        
        audio_file = self.audio_dir / self.current_poi['audio_file']
        
        if not audio_file.exists():
            print(f"Audio file not found: {audio_file}")
            self.ids.current_poi_label.text = f"Audio not found: {self.current_poi['name']}"
            return
        
        # Load and play with pygame
        self.current_audio_file = str(audio_file)
        pygame.mixer.music.load(self.current_audio_file)
        
        # Get audio length using pygame.mixer.Sound (load separately for duration)
        try:
            sound = pygame.mixer.Sound(self.current_audio_file)
            self.audio_length = sound.get_length()
            del sound  # Free memory
        except:
            self.audio_length = 0
        
        pygame.mixer.music.play()
        self.ids.play_btn.text = 'Pause'
        self.ids.current_poi_label.text = f"Playing: [b]{self.current_poi['num']}: {self.current_poi['name']}[/b]"
        
        # Set duration
        if self.audio_length > 0:
            self.ids.progress_slider.max = self.audio_length
            self.ids.duration_label.text = f"{int(self.audio_length // 60)}:{int(self.audio_length % 60):02d}"
        
        self._start_progress_update()
    
    def _start_progress_update(self):
        """Start updating progress bar."""
        Clock.unschedule(self._update_progress)
        Clock.schedule_interval(self._update_progress, 0.5)
    
    def _update_progress(self, dt):
        """Update progress bar and time labels using pygame."""
        # Check if audio finished
        if not pygame.mixer.music.get_busy() and self.current_audio_file and not self.is_paused:
            # Audio finished playing
            Clock.unschedule(self._update_progress)
            self.on_audio_complete()
            return
        
        # Get position from pygame (returns ms, -1 if not playing)
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms >= 0:
            pos = pos_ms / 1000.0 + self.seek_offset
        else:
            pos = self.seek_offset
        
        length = self.audio_length
        
        print(f"[PROGRESS] pos={pos:.2f}, length={length:.2f}")
        
        if length > 0:
            self.ids.progress_slider.max = length
            self.ids.progress_slider.value = min(pos, length)
            self.ids.time_label.text = f"{int(pos // 60)}:{int(pos % 60):02d}"
            self.ids.duration_label.text = f"{int(length // 60)}:{int(length % 60):02d}"
    
    def seek_audio(self, value):
        """Seek to a position in the audio."""
        if self.current_audio_file and self.audio_length > 0:
            print(f"[SEEK] seeking to {value:.2f}, length={self.audio_length:.2f}")
            # Restart playback from the new position
            pygame.mixer.music.stop()
            pygame.mixer.music.play(start=value)
            self.seek_offset = value
            self.is_paused = False
    
    def stop_audio(self):
        """Stop any currently playing audio and clear selection."""
        Clock.unschedule(self._update_progress)
        pygame.mixer.music.stop()
        self.seek_offset = 0
        self.is_paused = False
        self.audio_length = 0
        self.current_audio_file = None
        self.current_poi = None
        # Reset all UI
        self.ids.current_poi_label.text = 'Select a point of interest'
        self.ids.play_btn.text = 'Play'
        self.ids.play_btn.disabled = True
        self.ids.stop_btn.disabled = True
        self.ids.text_toggle.disabled = True
        self.ids.text_toggle.state = 'normal'
        self.ids.progress_slider.value = 0
        self.ids.progress_slider.max = 100
        self.ids.time_label.text = '0:00'
        self.ids.duration_label.text = '0:00'
        # Hide text panel (slide off-screen)
        self.ids.text_panel.pos_hint = {'x': 0, 'y': -0.46}
        self.ids.text_panel.opacity = 0
        self.ids.text_panel.disabled = True
        self.ids.poi_text_label.text = ''
        # Close all popups
        self.ids.map_widget.close_all_popups()
    
    def on_audio_complete(self):
        """Called when audio playback completes."""
        Clock.unschedule(self._update_progress)
        self.seek_offset = 0
        self.is_paused = False
        self.ids.play_btn.text = 'Play'
        self.ids.progress_slider.value = 0
        self.ids.time_label.text = '0:00'
        print("[COMPLETE] Audio finished")
    
    def toggle_gps(self, state):
        """Enable or disable GPS tracking."""
        if state == 'down':
            self.start_gps()
        else:
            self.stop_gps()
    
    def start_gps(self):
        """Start GPS tracking."""
        if not GPS_AVAILABLE:
            print("GPS not available - starting simulation")
            self.gps_enabled = True
            Clock.schedule_interval(self.simulate_gps, 2.0)
            return
        
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION
            ])
        
        try:
            gps.configure(
                on_location=self.on_gps_location,
                on_status=self.on_gps_status
            )
            gps.start(minTime=1000, minDistance=1)
            self.gps_enabled = True
            print("GPS started")
        except Exception as e:
            print(f"GPS error: {e}")
            self.gps_enabled = False
    
    def stop_gps(self):
        """Stop GPS tracking."""
        self.gps_enabled = False
        Clock.unschedule(self.simulate_gps)
        
        if GPS_AVAILABLE:
            try:
                gps.stop()
            except:
                pass
    
    def simulate_gps(self, dt):
        """Simulate GPS movement for testing."""
        import random
        if self.user_lat == 0 and self.pois:
            self.user_lat = self.pois[0]['lat']
            self.user_lon = self.pois[0]['lon']
        else:
            self.user_lat += random.uniform(-0.001, 0.001)
            self.user_lon += random.uniform(-0.001, 0.001)
        
        self.on_gps_location(lat=self.user_lat, lon=self.user_lon)
    
    def on_gps_location(self, **kwargs):
        """Handle GPS location update."""
        lat = kwargs.get('lat', 0)
        lon = kwargs.get('lon', 0)
        
        self.user_lat = lat
        self.user_lon = lon
        
        self.ids.map_widget.update_user_location(lat, lon)
        self.check_poi_proximity()
        
        # Update current POI label with distance if a POI is selected
        if self.current_poi and not pygame.mixer.music.get_busy():
            distance = haversine_distance(lat, lon, self.current_poi['lat'], self.current_poi['lon'])
            self.ids.current_poi_label.text = f"[b]{self.current_poi['num']}: {self.current_poi['name']}[/b] ({distance:.0f}m)"
    
    def on_gps_status(self, status, **kwargs):
        """Handle GPS status changes."""
        print(f"GPS status: {status}")
    
    def check_poi_proximity(self):
        """Check if user is near any POI and trigger audio."""
        if not self.gps_enabled:
            return
        
        for poi in self.pois:
            distance = haversine_distance(
                self.user_lat, self.user_lon,
                poi['lat'], poi['lon']
            )
            
            if distance <= self.trigger_radius and poi['num'] not in self.played_pois:
                self.played_pois.append(poi['num'])
                self.select_poi(poi)
                self.play_audio(poi)
                self.ids.map_widget.center_on_location(poi['lat'], poi['lon'])
                break
    
    def update_radius(self, value):
        """Update the trigger radius."""
        self.trigger_radius = value
        self.ids.radius_label.text = f"{int(value)}m"
    
    def show_poi_list(self):
        """Show a popup with all POIs."""
        popup = POIListPopup()
        
        for poi in self.pois:
            btn = Button(
                text=f"{poi['num']:02d}. {poi['name']}",
                size_hint_y=None,
                height=50,
                font_size='13sp',
                halign='left',
            )
            btn.bind(on_release=partial(self.on_list_item_click, poi, popup))
            popup.ids.poi_list.add_widget(btn)
        
        popup.open()
    
    def on_list_item_click(self, poi, popup, button):
        """Handle POI list item click."""
        popup.dismiss()
        self.select_poi(poi)
        self.ids.map_widget.center_on_location(poi['lat'], poi['lon'], zoom=14)
    
    def reset_played_pois(self):
        """Reset the list of auto-played POIs."""
        self.played_pois = []


class CaminoApp(App):
    """Main application class."""
    
    def build(self):
        Builder.load_string(KV)
        
        self.sm = ScreenManager()
        
        # Add screens
        self.tour_select_screen = TourSelectScreen(name='tour_select')
        self.tour_screen = TourScreen(name='tour')
        
        self.sm.add_widget(self.tour_select_screen)
        self.sm.add_widget(self.tour_screen)
        
        return self.sm
    
    def open_tour(self, tour):
        """Open a specific tour."""
        self.tour_screen.load_tour(tour)
        self.sm.transition = SlideTransition(direction='left')
        self.sm.current = 'tour'
    
    def show_tour_select(self):
        """Return to tour selection screen."""
        self.sm.transition = SlideTransition(direction='right')
        self.sm.current = 'tour_select'
    
    def on_pause(self):
        """Handle app pause (Android)."""
        return True
    
    def on_resume(self):
        """Handle app resume (Android)."""
        pass


if __name__ == '__main__':
    CaminoApp().run()
