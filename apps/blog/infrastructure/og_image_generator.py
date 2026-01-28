"""
OG Image Generator for Blog Posts.

Generates Open Graph images for social media sharing using a consistent
template that aligns with the site's dark theme and blue accents.
"""
import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class BlogOGImageGenerator:
    """Generates OG images for blog posts."""
    
    # OG image dimensions (standard for social platforms)
    WIDTH = 1200
    HEIGHT = 630
    
    # Color palette matching site theme
    COLORS = {
        'background': (10, 10, 15),        # #0a0a0f - dark background
        'gradient_end': (20, 20, 35),      # Slightly lighter for gradient
        'title': (255, 255, 255),          # White
        'subtitle': (156, 163, 175),       # Gray-400
        'accent': (59, 130, 246),          # Blue-500
        'accent_light': (96, 165, 250),    # Blue-400
        'tag_bg': (30, 30, 45),            # Dark tag background
    }
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory to save generated images. 
                       Defaults to staticfiles/og-images/
        """
        if output_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            output_dir = base_dir / 'staticfiles' / 'og-images'
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load fonts
        self._load_fonts()
    
    def _load_fonts(self):
        """Load system fonts with fallbacks."""
        # Windows font paths
        font_paths = [
            'C:/Windows/Fonts/segoeuib.ttf',   # Segoe UI Bold
            'C:/Windows/Fonts/segoeui.ttf',    # Segoe UI Regular
            'C:/Windows/Fonts/arial.ttf',       # Arial fallback
        ]
        
        # Try to load fonts
        self.title_font = None
        self.subtitle_font = None
        self.tag_font = None
        self.author_font = None
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if 'bold' in font_path.lower() or 'segoeuib' in font_path.lower():
                        self.title_font = ImageFont.truetype(font_path, 52)
                    else:
                        self.subtitle_font = ImageFont.truetype(font_path, 24)
                        self.tag_font = ImageFont.truetype(font_path, 18)
                        self.author_font = ImageFont.truetype(font_path, 20)
                except Exception:
                    continue
        
        # Fallback to default font if needed
        if self.title_font is None:
            self.title_font = ImageFont.load_default()
        if self.subtitle_font is None:
            self.subtitle_font = ImageFont.load_default()
        if self.tag_font is None:
            self.tag_font = ImageFont.load_default()
        if self.author_font is None:
            self.author_font = ImageFont.load_default()
    
    def _create_gradient_background(self) -> Image.Image:
        """Create a dark gradient background matching site theme."""
        import numpy as np
        
        # Use numpy for fast gradient generation
        x = np.linspace(0, 1, self.WIDTH)
        y = np.linspace(0, 1, self.HEIGHT)
        xx, yy = np.meshgrid(x, y)
        
        # Diagonal gradient factor
        factor = (xx * 0.3) + (yy * 0.3)
        
        # Calculate RGB channels
        r = (self.COLORS['background'][0] + factor * 15).astype(np.uint8)
        g = (self.COLORS['background'][1] + factor * 10).astype(np.uint8)
        b = (self.COLORS['background'][2] + factor * 25).astype(np.uint8)
        
        # Stack and create image
        rgb = np.stack([r, g, b], axis=-1)
        img = Image.fromarray(rgb, 'RGB')
        
        return img
    
    def _wrap_text(self, text: str, max_chars: int = 35) -> list[str]:
        """Wrap text to fit within image bounds."""
        return textwrap.wrap(text, width=max_chars)
    
    def generate(
        self,
        title: str,
        slug: str,
        tags: list[str] = None,
        author: str = "Joseph Prince",
        reading_time: int = None,
    ) -> str:
        """
        Generate an OG image for a blog post.
        
        Args:
            title: Blog post title
            slug: URL slug (used for filename)
            tags: List of post tags
            author: Author name
            reading_time: Estimated reading time in minutes
            
        Returns:
            Relative URL path to the generated image
        """
        # Create base image with gradient
        img = self._create_gradient_background()
        draw = ImageDraw.Draw(img)
        
        # Add decorative elements
        
        # Blue accent bar at top
        draw.rectangle([0, 0, self.WIDTH, 4], fill=self.COLORS['accent'])
        
        # Subtle grid pattern (very faint)
        for x in range(0, self.WIDTH, 60):
            draw.line([(x, 0), (x, self.HEIGHT)], fill=(20, 20, 30), width=1)
        for y in range(0, self.HEIGHT, 60):
            draw.line([(0, y), (self.WIDTH, y)], fill=(20, 20, 30), width=1)
        
        # Blue accent line on left
        draw.rectangle([60, 180, 64, 280], fill=self.COLORS['accent'])
        
        # Content area
        content_x = 80
        current_y = 200
        
        # Draw title (wrapped if needed)
        title_lines = self._wrap_text(title, max_chars=32)
        for line in title_lines[:3]:  # Max 3 lines
            # Shadow
            draw.text(
                (content_x + 2, current_y + 2),
                line,
                font=self.title_font,
                fill=(0, 0, 0)
            )
            # Main text
            draw.text(
                (content_x, current_y),
                line,
                font=self.title_font,
                fill=self.COLORS['title']
            )
            current_y += 60
        
        # Add spacing
        current_y += 20
        
        # Draw tags if provided
        if tags and len(tags) > 0:
            tag_x = content_x
            for tag in tags[:4]:  # Max 4 tags
                tag_text = f"#{tag}"
                # Get text size
                bbox = draw.textbbox((0, 0), tag_text, font=self.tag_font)
                tag_width = bbox[2] - bbox[0] + 20
                
                # Draw tag pill
                draw.rounded_rectangle(
                    [tag_x, current_y, tag_x + tag_width, current_y + 30],
                    radius=15,
                    fill=self.COLORS['tag_bg']
                )
                draw.text(
                    (tag_x + 10, current_y + 5),
                    tag_text,
                    font=self.tag_font,
                    fill=self.COLORS['accent_light']
                )
                tag_x += tag_width + 10
            
            current_y += 50
        
        # Draw author and reading time at bottom
        bottom_y = self.HEIGHT - 80
        author_text = f"By {author}"
        if reading_time:
            author_text += f"  •  {reading_time} min read"
        
        draw.text(
            (content_x, bottom_y),
            author_text,
            font=self.author_font,
            fill=self.COLORS['subtitle']
        )
        
        # Site branding in bottom right
        brand_text = "www.thejosephprince.com"
        bbox = draw.textbbox((0, 0), brand_text, font=self.author_font)
        brand_width = bbox[2] - bbox[0]
        draw.text(
            (self.WIDTH - brand_width - 60, bottom_y),
            brand_text,
            font=self.author_font,
            fill=self.COLORS['accent_light']
        )
        
        # Save image
        filename = f"{slug}.png"
        filepath = self.output_dir / filename
        img.save(filepath, 'PNG', quality=95)
        
        # Return URL path
        return f"/static/og-images/{filename}"
    
    def generate_for_post(self, post) -> str:
        """
        Generate OG image from a BlogPost entity.
        
        Args:
            post: BlogPost domain entity
            
        Returns:
            Relative URL path to the generated image
        """
        tags = [str(t) for t in post.tags] if post.tags else []
        
        return self.generate(
            title=post.title,
            slug=str(post.slug),
            tags=tags,
            author=post.author_name or "Joseph Prince",
            reading_time=post.reading_time,
        )


# Singleton instance for easy access
_generator = None

def get_og_image_generator() -> BlogOGImageGenerator:
    """Get the singleton OG image generator instance."""
    global _generator
    if _generator is None:
        _generator = BlogOGImageGenerator()
    return _generator


def generate_og_image_for_post(post) -> str:
    """
    Convenience function to generate OG image for a blog post.
    
    Args:
        post: BlogPost entity or model with title, slug, tags, author_name
        
    Returns:
        URL path to the generated image
    """
    generator = get_og_image_generator()
    return generator.generate_for_post(post)
