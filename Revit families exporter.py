# -*- coding: utf-8 -*-
from pyrevit import revit, forms
from Autodesk.Revit.DB import *
import clr
import os

doc = revit.doc

# ----------------------------
# WPF IMPORTS
# ----------------------------
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

from System.Windows import (
    Window, Thickness, SizeToContent, HorizontalAlignment,
    VerticalAlignment, ResizeMode, GridLength, GridUnitType,
    TextAlignment, CornerRadius
)
from System.Windows.Controls import (
    Grid, StackPanel, ScrollViewer, TextBox, TextBlock, ComboBox,
    Button, CheckBox, RowDefinition, ColumnDefinition, Orientation,
    ScrollBarVisibility, Border
)
from System.Windows.Media import (
    Brushes, LinearGradientBrush, GradientStop, GradientStopCollection,
    Color, SolidColorBrush
)
from System.Windows import FontWeights
from System.Windows.Input import Cursors
from System.Windows.Markup import XamlReader

import System.Windows
FontFamily = System.Windows.Media.FontFamily

# ----------------------------
# COLOR HELPERS
# ----------------------------
def rgb(r, g, b, a=255):
    return SolidColorBrush(Color.FromArgb(a, r, g, b))

def gradient(c1, c2, angle=90):
    return LinearGradientBrush(
        GradientStopCollection([
            GradientStop(Color.FromArgb(255, *c1), 0.0),
            GradientStop(Color.FromArgb(255, *c2), 1.0),
        ]),
        angle
    )

def gradient_multi(stops, angle=90):
    coll = GradientStopCollection()
    for offset, rgba in stops:
        coll.Add(GradientStop(Color.FromArgb(*rgba), offset))
    return LinearGradientBrush(coll, angle)

# ----------------------------
# THEME COLORS
# ----------------------------
C_BG_DEEP     = rgb(12, 14, 22)
C_BG_PANEL    = rgb(18, 21, 34)
C_BG_CARD     = rgb(24, 28, 46)
C_BG_INPUT    = rgb(30, 35, 56)
C_BG_ALT      = rgb(20, 24, 40)
C_BORDER      = rgb(55, 65, 100)
C_BORDER_LT   = rgb(80, 100, 160)

C_NEON_CYAN   = rgb(0, 210, 255)
C_NEON_PURPLE = rgb(160, 80, 255)
C_NEON_GREEN  = rgb(40, 220, 130)
C_NEON_ORANGE = rgb(255, 140, 40)
C_NEON_RED    = rgb(255, 70, 90)

C_TEXT_PRIMARY = rgb(220, 230, 255)
C_TEXT_DIM     = rgb(80, 100, 150)

GRAD_HEADER   = gradient_multi(
    [(0.0,(255,20,140,255)),(0.5,(120,40,255,255)),(1.0,(0,180,255,255))], 0)
GRAD_EXPORT   = gradient((20, 200, 120), (0, 160, 255))
GRAD_SELECT   = gradient((40, 180, 255), (80, 100, 255))
GRAD_DESELECT = gradient((255, 80, 120), (200, 50, 80))
GRAD_BROWSE   = gradient((255, 140, 30), (255, 60, 130))

# ----------------------------
# DATA
# ----------------------------
def get_families():
    collector = FilteredElementCollector(doc).OfClass(Family)
    categories = {}
    all_fams = []
    for fam in collector:
        cat = fam.FamilyCategory
        if not cat:
            continue
        cat_name = cat.Name
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(fam)
        all_fams.append(fam)
    return categories, all_fams

categories, all_families = get_families()
selected_path = None
checkbox_map = []

# ----------------------------
# NEON DIVIDER
# ----------------------------
def neon_divider(margin_tb=4):
    b = Border()
    b.Height = 2
    b.Margin = Thickness(0, margin_tb, 0, margin_tb)
    b.Background = gradient_multi([
        (0.0,(0,0,0,0)),
        (0.3,(0,210,255,180)),
        (0.7,(160,80,255,180)),
        (1.0,(0,0,0,0))
    ], 0)
    return b

# ----------------------------
# STAT BADGE
# ----------------------------
def make_badge(label_text, value_text, accent):
    panel = StackPanel()
    panel.Orientation = Orientation.Vertical
    panel.HorizontalAlignment = HorizontalAlignment.Center

    val = TextBlock()
    val.Text = value_text
    val.FontSize = 18
    val.FontWeight = FontWeights.Bold
    val.Foreground = accent
    val.TextAlignment = TextAlignment.Center
    val.FontFamily = FontFamily("Consolas")

    lbl = TextBlock()
    lbl.Text = label_text
    lbl.FontSize = 9
    lbl.Foreground = C_TEXT_DIM
    lbl.TextAlignment = TextAlignment.Center
    lbl.FontFamily = FontFamily("Consolas")

    panel.Children.Add(val)
    panel.Children.Add(lbl)

    b = Border()
    b.CornerRadius = CornerRadius(6)
    b.Background = C_BG_INPUT
    b.BorderBrush = accent
    b.BorderThickness = Thickness(1)
    b.Padding = Thickness(12, 5, 12, 5)
    b.Child = panel
    return b, val

# ----------------------------
# SECTION LABEL ROW
# ----------------------------
def sec_label(icon, title, color, hint=""):
    sp = StackPanel()
    sp.Orientation = Orientation.Horizontal
    sp.Margin = Thickness(0, 0, 0, 4)

    ic = TextBlock()
    ic.Text = icon
    ic.FontSize = 12
    ic.Margin = Thickness(0, 0, 5, 0)
    ic.VerticalAlignment = VerticalAlignment.Center

    ti = TextBlock()
    ti.Text = title
    ti.FontSize = 10
    ti.FontWeight = FontWeights.Bold
    ti.Foreground = color
    ti.FontFamily = FontFamily("Consolas")
    ti.VerticalAlignment = VerticalAlignment.Center

    sp.Children.Add(ic)
    sp.Children.Add(ti)

    if hint:
        ht = TextBlock()
        ht.Text = "  " + hint
        ht.FontSize = 9
        ht.Foreground = C_TEXT_DIM
        ht.FontFamily = FontFamily("Consolas")
        ht.VerticalAlignment = VerticalAlignment.Center
        sp.Children.Add(ht)

    return sp

# ----------------------------
# STYLED BUTTON
# ----------------------------
def make_btn(text, bg, h=30, w=0, font_size=11):
    b = Button()
    b.Content = text
    b.Height = h
    if w:
        b.Width = w
    b.Background = bg
    b.Foreground = Brushes.White
    b.FontWeight = FontWeights.Bold
    b.FontSize = font_size
    b.FontFamily = FontFamily("Consolas")
    b.BorderThickness = Thickness(0)
    b.Cursor = Cursors.Hand
    return b

# ============================================================
# COMBOBOX FULL STYLE via ControlTemplate
# FIX: Added xmlns:x namespace declaration to both XAML blocks
#      so that x:Name attributes are recognised by XamlReader.Parse()
# ============================================================
def apply_combobox_style(cb,
                          bg_hex="#1a1d32",
                          fg_hex="#dce6ff",
                          bdr_hex="#a050ff",
                          drp_hex="#12152a",
                          item_hover_hex="#2a1a5a"):
    xaml = """
<ControlTemplate
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    TargetType="ComboBox">

  <Grid>
    <!-- Main box -->
    <Border x:Name="MainBorder"
            Background="{BG}"
            BorderBrush="{BDR}"
            BorderThickness="1"
            CornerRadius="5">
      <Grid>
        <Grid.ColumnDefinitions>
          <ColumnDefinition />
          <ColumnDefinition Width="26" />
        </Grid.ColumnDefinitions>

        <!-- Selected item text -->
        <ContentPresenter
            Grid.Column="0"
            Margin="9,0,4,0"
            VerticalAlignment="Center"
            HorizontalAlignment="Left"
            Content="{TemplateBinding SelectionBoxItem}"
            ContentTemplate="{TemplateBinding SelectionBoxItemTemplate}"
            ContentTemplateSelector="{TemplateBinding ItemTemplateSelector}"
            IsHitTestVisible="False" />

        <!-- Arrow button -->
        <ToggleButton
            Grid.Column="1"
            Background="Transparent"
            BorderThickness="0"
            Focusable="False"
            ClickMode="Press"
            IsChecked="{Binding Path=IsDropDownOpen,
                         RelativeSource={RelativeSource TemplatedParent},
                         Mode=TwoWay}">
          <Path Data="M 0 0 L 7 7 L 14 0 Z"
                Fill="{BDR}"
                HorizontalAlignment="Center"
                VerticalAlignment="Center"
                Width="14" Height="7" />
        </ToggleButton>
      </Grid>
    </Border>

    <!-- Dropdown popup -->
    <Popup
        x:Name="PART_Popup"
        AllowsTransparency="True"
        IsOpen="{Binding IsDropDownOpen,
                  RelativeSource={RelativeSource TemplatedParent}}"
        Placement="Bottom"
        PopupAnimation="Slide">
      <Border
          Background="{DRP}"
          BorderBrush="{BDR}"
          BorderThickness="1"
          CornerRadius="5"
          MinWidth="{Binding ActualWidth,
                     RelativeSource={RelativeSource TemplatedParent}}"
          MaxHeight="{TemplateBinding MaxDropDownHeight}">
        <ScrollViewer VerticalScrollBarVisibility="Auto">
          <ItemsPresenter />
        </ScrollViewer>
      </Border>
    </Popup>
  </Grid>

  <!-- Triggers -->
  <ControlTemplate.Triggers>
    <Trigger Property="IsMouseOver" Value="True">
      <Setter TargetName="MainBorder" Property="BorderBrush" Value="{BDR_BRIGHT}" />
      <Setter TargetName="MainBorder" Property="Background"  Value="{BG_HOVER}" />
    </Trigger>
  </ControlTemplate.Triggers>
</ControlTemplate>
""".replace("{BG}",       bg_hex) \
   .replace("{BDR}",      bdr_hex) \
   .replace("{DRP}",      drp_hex) \
   .replace("{BDR_BRIGHT}", "#c880ff") \
   .replace("{BG_HOVER}",  "#22193a")

    cb.Template = XamlReader.Parse(xaml)

    # Style individual items inside the dropdown
    item_xaml = """
<Style
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    TargetType="ComboBoxItem">
  <Setter Property="Background"        Value="{DRP}" />
  <Setter Property="Foreground"        Value="{FG}" />
  <Setter Property="FontFamily"        Value="Consolas" />
  <Setter Property="FontSize"          Value="12" />
  <Setter Property="Padding"           Value="9,5,9,5" />
  <Setter Property="HorizontalContentAlignment" Value="Left" />
  <Setter Property="Template">
    <Setter.Value>
      <ControlTemplate TargetType="ComboBoxItem">
        <Border x:Name="Bd"
                Background="{TemplateBinding Background}"
                Padding="{TemplateBinding Padding}">
          <ContentPresenter />
        </Border>
        <ControlTemplate.Triggers>
          <Trigger Property="IsHighlighted" Value="True">
            <Setter TargetName="Bd" Property="Background" Value="{HOVER}" />
          </Trigger>
          <Trigger Property="IsSelected" Value="True">
            <Setter TargetName="Bd" Property="Background" Value="{SEL}" />
          </Trigger>
        </ControlTemplate.Triggers>
      </ControlTemplate>
    </Setter.Value>
  </Setter>
</Style>
""".replace("{DRP}",  drp_hex) \
   .replace("{FG}",   fg_hex) \
   .replace("{HOVER}", item_hover_hex) \
   .replace("{SEL}",  "#3a1f6a")

    cb.ItemContainerStyle = XamlReader.Parse(item_xaml)
    cb.Foreground = SolidColorBrush(Color.FromArgb(
        255,
        int(fg_hex[1:3], 16),
        int(fg_hex[3:5], 16),
        int(fg_hex[5:7], 16)
    ))
    cb.FontFamily = FontFamily("Consolas")
    cb.FontSize = 12

# ============================================================
# MAIN WINDOW
# Root = 3-row Grid:
#   Row 0 (Auto) = header + stats + search/category + buttons + list label
#   Row 1 (Star) = scrollable family list
#   Row 2 (Auto) = output path + export btn + footer
# ============================================================
class FamilyExporter(Window):
    def __init__(self):
        self.Title = "⚡ Family Exporter Pro  |  pyRevit"
        self.Width  = 760
        self.Height = 820
        self.MinWidth  = 680
        self.MinHeight = 700
        self.Background = C_BG_DEEP
        self.SizeToContent = SizeToContent.Manual
        self.ResizeMode = ResizeMode.CanResize
        self.WindowStartupLocation = System.Windows.WindowStartupLocation.CenterScreen

        # ROOT GRID
        root = Grid()
        self.Content = root

        root.RowDefinitions.Add(RowDefinition())
        root.RowDefinitions[0].Height = GridLength.Auto           # top fixed
        root.RowDefinitions.Add(RowDefinition())
        root.RowDefinitions[1].Height = GridLength(1, GridUnitType.Star)  # list stretches
        root.RowDefinitions.Add(RowDefinition())
        root.RowDefinitions[2].Height = GridLength.Auto           # bottom fixed

        # ══════════════════════════════════════════
        # ROW 0 — TOP FIXED CONTROLS
        # ══════════════════════════════════════════
        top = StackPanel()
        top.Orientation = Orientation.Vertical
        Grid.SetRow(top, 0)
        root.Children.Add(top)

        # -- Header banner --
        hdr = Border()
        hdr.Background = GRAD_HEADER
        hdr.Padding = Thickness(20, 13, 20, 13)
        hdr_inner = StackPanel()
        hdr_inner.HorizontalAlignment = HorizontalAlignment.Center

        t1 = TextBlock()
        t1.Text = "⚡  FAMILY EXPORTER PRO"
        t1.FontSize = 23
        t1.FontWeight = FontWeights.Bold
        t1.Foreground = Brushes.White
        t1.FontFamily = FontFamily("Consolas")
        t1.TextAlignment = TextAlignment.Center

        t2 = TextBlock()
        t2.Text = "Batch export Revit families with precision & speed"
        t2.FontSize = 11
        t2.Foreground = rgb(200, 210, 255, 160)
        t2.FontFamily = FontFamily("Consolas")
        t2.TextAlignment = TextAlignment.Center
        t2.Margin = Thickness(0, 3, 0, 0)

        hdr_inner.Children.Add(t1)
        hdr_inner.Children.Add(t2)
        hdr.Child = hdr_inner
        top.Children.Add(hdr)

        # -- Stats badges --
        stats_sp = StackPanel()
        stats_sp.Orientation = Orientation.Horizontal
        stats_sp.HorizontalAlignment = HorizontalAlignment.Center
        stats_sp.Margin = Thickness(0, 7, 0, 2)

        total_b, _              = make_badge("TOTAL FAMILIES", str(len(all_families)), C_NEON_CYAN)
        cat_b,   _              = make_badge("CATEGORIES",     str(len(categories)),   C_NEON_PURPLE)
        sel_b,   self.stat_sel  = make_badge("SELECTED",       "0",                    C_NEON_GREEN)
        show_b,  self.stat_show = make_badge("SHOWING",        "0",                    C_NEON_ORANGE)

        for badge in [total_b, cat_b, sel_b, show_b]:
            badge.Margin = Thickness(5, 0, 5, 0)
            stats_sp.Children.Add(badge)
        top.Children.Add(stats_sp)
        top.Children.Add(neon_divider(5))

        # -- Search + Category side by side --
        ctrl_grid = Grid()
        ctrl_grid.Margin = Thickness(14, 0, 14, 4)
        ctrl_grid.ColumnDefinitions.Add(ColumnDefinition())
        ctrl_grid.ColumnDefinitions.Add(ColumnDefinition())

        # Search box (left)
        search_col = StackPanel()
        search_col.Margin = Thickness(0, 0, 6, 0)
        search_col.Children.Add(
            sec_label("🔍", "SEARCH FAMILIES", C_NEON_CYAN, "filter across all"))

        self.search = TextBox()
        self.search.Height = 28
        self.search.Background = C_BG_INPUT
        self.search.Foreground = C_TEXT_PRIMARY
        self.search.CaretBrush = C_NEON_CYAN
        self.search.FontSize = 12
        self.search.FontFamily = FontFamily("Consolas")
        self.search.Padding = Thickness(7, 3, 7, 3)
        self.search.BorderBrush = C_NEON_CYAN
        self.search.BorderThickness = Thickness(0, 0, 0, 2)
        self.search.TextChanged += self.on_search
        search_col.Children.Add(self.search)
        Grid.SetColumn(search_col, 0)
        ctrl_grid.Children.Add(search_col)

        # Category dropdown (right)
        cat_col = StackPanel()
        cat_col.Margin = Thickness(6, 0, 0, 0)
        cat_col.Children.Add(
            sec_label("📂", "FILTER BY CATEGORY", C_NEON_PURPLE))

        self.dropdown = ComboBox()
        self.dropdown.Height = 28
        self.dropdown.Items.Add("— All Categories —")
        for cat in sorted(categories.keys()):
            self.dropdown.Items.Add(cat)
        self.dropdown.SelectedIndex = 0
        self.dropdown.SelectionChanged += self.load_families

        # Apply full custom style — bypasses Windows theme completely
        apply_combobox_style(
            self.dropdown,
            bg_hex       = "#1a1230",
            fg_hex       = "#dce6ff",
            bdr_hex      = "#a050ff",
            drp_hex      = "#110d22",
            item_hover_hex = "#2e1a55"
        )

        cat_col.Children.Add(self.dropdown)
        Grid.SetColumn(cat_col, 1)
        ctrl_grid.Children.Add(cat_col)

        top.Children.Add(ctrl_grid)

        # -- Select / Deselect buttons --
        btn_row = StackPanel()
        btn_row.Orientation = Orientation.Horizontal
        btn_row.Margin = Thickness(14, 4, 14, 3)

        self.sel_btn = make_btn("✅  Select All",   GRAD_SELECT,   h=26, w=115)
        self.sel_btn.Margin = Thickness(0, 0, 7, 0)
        self.sel_btn.Click += self.select_all_families
        btn_row.Children.Add(self.sel_btn)

        self.des_btn = make_btn("❌  Deselect All", GRAD_DESELECT, h=26, w=115)
        self.des_btn.Click += self.deselect_all_families
        btn_row.Children.Add(self.des_btn)

        self.count_lbl = TextBlock()
        self.count_lbl.Text = "0 families selected"
        self.count_lbl.Foreground = C_TEXT_DIM
        self.count_lbl.FontSize = 10
        self.count_lbl.FontFamily = FontFamily("Consolas")
        self.count_lbl.VerticalAlignment = VerticalAlignment.Center
        self.count_lbl.Margin = Thickness(10, 0, 0, 0)
        btn_row.Children.Add(self.count_lbl)
        top.Children.Add(btn_row)

        # -- Family list label --
        lbl_sp = StackPanel()
        lbl_sp.Margin = Thickness(14, 3, 14, 2)
        lbl_sp.Children.Add(sec_label("📋", "FAMILY LIST", C_NEON_GREEN))
        top.Children.Add(lbl_sp)

        # ══════════════════════════════════════════
        # ROW 1 — SCROLLABLE LIST (stretches)
        # ══════════════════════════════════════════
        scroll_border = Border()
        scroll_border.Margin = Thickness(14, 0, 14, 0)
        scroll_border.CornerRadius = CornerRadius(7)
        scroll_border.BorderBrush = C_BORDER
        scroll_border.BorderThickness = Thickness(1)
        scroll_border.Background = C_BG_PANEL
        Grid.SetRow(scroll_border, 1)
        root.Children.Add(scroll_border)

        self.scroll = ScrollViewer()
        self.scroll.VerticalScrollBarVisibility = ScrollBarVisibility.Auto
        self.scroll.HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled

        self.panel = StackPanel()
        self.panel.Margin = Thickness(3)
        self.scroll.Content = self.panel
        scroll_border.Child = self.scroll

        # ══════════════════════════════════════════
        # ROW 2 — BOTTOM FIXED: PATH + EXPORT + FOOTER
        # ══════════════════════════════════════════
        bot = StackPanel()
        bot.Orientation = Orientation.Vertical
        bot.Margin = Thickness(14, 5, 14, 0)
        Grid.SetRow(bot, 2)
        root.Children.Add(bot)

        bot.Children.Add(neon_divider(3))
        bot.Children.Add(
            sec_label("💾", "OUTPUT FOLDER", C_NEON_ORANGE, "paste a path directly or browse"))

        # Path input + Browse button
        path_g = Grid()
        path_g.Margin = Thickness(0, 0, 0, 5)
        path_g.ColumnDefinitions.Add(ColumnDefinition())
        pc2 = ColumnDefinition(); pc2.Width = GridLength.Auto
        path_g.ColumnDefinitions.Add(pc2)

        self.path_input = TextBox()
        self.path_input.Height = 28
        self.path_input.Background = C_BG_INPUT
        self.path_input.Foreground = rgb(255, 200, 60)
        self.path_input.CaretBrush = C_NEON_ORANGE
        self.path_input.FontSize = 12
        self.path_input.FontFamily = FontFamily("Consolas")
        self.path_input.Padding = Thickness(7, 3, 7, 3)
        self.path_input.BorderBrush = C_NEON_ORANGE
        self.path_input.BorderThickness = Thickness(1, 1, 0, 2)
        self.path_input.ToolTip = "Paste or type an output folder path here"
        self.path_input.TextChanged += self.on_path_typed
        Grid.SetColumn(self.path_input, 0)
        path_g.Children.Add(self.path_input)

        self.browse_btn = make_btn("📁  Browse", GRAD_BROWSE, h=28, w=95)
        self.browse_btn.Click += self.browse_folder
        Grid.SetColumn(self.browse_btn, 1)
        path_g.Children.Add(self.browse_btn)

        bot.Children.Add(path_g)

        # Export button
        self.export_btn = make_btn(
            "🚀   EXPORT SELECTED FAMILIES", GRAD_EXPORT, h=42, font_size=14)
        self.export_btn.Margin = Thickness(0, 0, 0, 0)
        self.export_btn.Click += self.export_families
        bot.Children.Add(self.export_btn)

        # Footer
        footer = TextBlock()
        footer.Text = "pyRevit  ·  Family Exporter Pro  ·  Powered by Autodesk Revit API"
        footer.FontSize = 9
        footer.Foreground = C_TEXT_DIM
        footer.FontFamily = FontFamily("Consolas")
        footer.HorizontalAlignment = HorizontalAlignment.Center
        footer.Margin = Thickness(0, 5, 0, 8)
        bot.Children.Add(footer)

        # Init
        self.populate_list(all_families)
        self.update_stats()

    # ----------------------------
    # POPULATE LIST
    # ----------------------------
    def populate_list(self, fam_list):
        self.panel.Children.Clear()
        checkbox_map[:] = []

        if not fam_list:
            empty = TextBlock()
            empty.Text = "  No families found."
            empty.Foreground = C_TEXT_DIM
            empty.FontSize = 12
            empty.FontFamily = FontFamily("Consolas")
            empty.Margin = Thickness(10, 8, 10, 8)
            self.panel.Children.Add(empty)
            self.update_stats()
            return

        for idx, fam in enumerate(fam_list):
            row = Border()
            row.Margin = Thickness(2, 1, 2, 1)
            row.Padding = Thickness(8, 3, 8, 3)
            row.CornerRadius = CornerRadius(4)
            row.Background = C_BG_CARD if idx % 2 == 0 else C_BG_ALT
            row.BorderBrush = C_BORDER
            row.BorderThickness = Thickness(1)

            row_inner = Grid()
            row_inner.ColumnDefinitions.Add(ColumnDefinition())
            ri_c2 = ColumnDefinition(); ri_c2.Width = GridLength.Auto
            row_inner.ColumnDefinitions.Add(ri_c2)

            cb = CheckBox()
            cb.Foreground = C_TEXT_PRIMARY
            cb.FontSize = 12
            cb.FontFamily = FontFamily("Consolas")
            cb.VerticalAlignment = VerticalAlignment.Center
            cb.Tag = fam
            cb.Checked   += self.on_check_changed
            cb.Unchecked += self.on_check_changed

            name_tb = TextBlock()
            name_tb.Text = "  " + fam.Name
            name_tb.Foreground = C_TEXT_PRIMARY
            name_tb.FontSize = 12
            name_tb.FontFamily = FontFamily("Consolas")
            name_tb.VerticalAlignment = VerticalAlignment.Center

            cb_row = StackPanel()
            cb_row.Orientation = Orientation.Horizontal
            cb_row.VerticalAlignment = VerticalAlignment.Center
            cb_row.Children.Add(cb)
            cb_row.Children.Add(name_tb)
            Grid.SetColumn(cb_row, 0)

            cat_pill = Border()
            cat_pill.CornerRadius = CornerRadius(3)
            cat_pill.Padding = Thickness(5, 1, 5, 1)
            cat_pill.Background = rgb(40, 50, 80)
            cat_pill.BorderBrush = C_NEON_PURPLE
            cat_pill.BorderThickness = Thickness(1)
            cat_pill.VerticalAlignment = VerticalAlignment.Center

            cat_tb = TextBlock()
            cat_tb.Text = fam.FamilyCategory.Name
            cat_tb.Foreground = C_NEON_PURPLE
            cat_tb.FontSize = 9
            cat_tb.FontFamily = FontFamily("Consolas")
            cat_pill.Child = cat_tb
            Grid.SetColumn(cat_pill, 1)

            row_inner.Children.Add(cb_row)
            row_inner.Children.Add(cat_pill)
            row.Child = row_inner
            self.panel.Children.Add(row)
            checkbox_map.append(cb)

        self.update_stats()

    # ----------------------------
    # LOAD CATEGORY
    # ----------------------------
    def load_families(self, sender, args):
        sel = self.dropdown.SelectedItem
        if not sel or sel == "— All Categories —":
            self.populate_list(all_families)
        else:
            self.populate_list(categories.get(sel, []))

    # ----------------------------
    # SEARCH
    # ----------------------------
    def on_search(self, sender, args):
        text = self.search.Text.lower().strip()
        if text:
            self.populate_list([f for f in all_families if text in f.Name.lower()])
        else:
            self.load_families(None, None)

    # ----------------------------
    # CHECK / COUNT
    # ----------------------------
    def on_check_changed(self, sender, args):
        self.update_count_label()

    def update_count_label(self):
        n = sum(1 for cb in checkbox_map if cb.IsChecked)
        self.count_lbl.Text = "{} famil{} selected".format(n, "y" if n == 1 else "ies")
        self.stat_sel.Text = str(n)

    def update_stats(self):
        self.stat_show.Text = str(len(checkbox_map))
        self.update_count_label()

    # ----------------------------
    # PATH TYPED
    # ----------------------------
    def on_path_typed(self, sender, args):
        global selected_path
        typed = self.path_input.Text.strip()
        if os.path.isdir(typed):
            selected_path = typed
            self.path_input.Foreground = C_NEON_GREEN
        else:
            selected_path = None
            self.path_input.Foreground = C_NEON_RED if typed else rgb(255, 200, 60)

    # ----------------------------
    # BROWSE
    # ----------------------------
    def browse_folder(self, sender, args):
        global selected_path
        folder = forms.pick_folder()
        if folder:
            selected_path = folder
            self.path_input.Text = folder
            self.path_input.Foreground = C_NEON_GREEN

    # ----------------------------
    # EXPORT
    # ----------------------------
    def export_families(self, sender, args):
        global selected_path
        if not selected_path or not os.path.isdir(selected_path):
            forms.alert("Please select or enter a valid output folder path.")
            return
        checked = [cb for cb in checkbox_map if cb.IsChecked]
        if not checked:
            forms.alert("No families selected. Check at least one family.")
            return
        count, errors = 0, []
        for cb in checked:
            fam = cb.Tag
            try:
                fam_doc  = doc.EditFamily(fam)
                save_opt = SaveAsOptions()
                save_opt.OverwriteExistingFile = True
                fam_doc.SaveAs(
                    os.path.join(selected_path, fam.Name + ".rfa"), save_opt)
                fam_doc.Close(False)
                count += 1
            except Exception as e:
                errors.append("{}: {}".format(fam.Name, e))
        msg = "✅  {} famil{} exported to:\n{}".format(
            count, "y" if count == 1 else "ies", selected_path)
        if errors:
            msg += "\n\n⚠️  {} error(s):\n".format(len(errors)) + "\n".join(errors[:5])
        forms.alert(msg)

    # ----------------------------
    # SELECT / DESELECT ALL
    # ----------------------------
    def select_all_families(self, sender, args):
        for cb in checkbox_map:
            cb.IsChecked = True
        self.update_stats()

    def deselect_all_families(self, sender, args):
        for cb in checkbox_map:
            cb.IsChecked = False
        self.update_stats()


# ----------------------------
# RUN
# ----------------------------
FamilyExporter().ShowDialog()
