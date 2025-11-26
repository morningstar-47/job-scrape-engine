"""Modèles de données pour les CV"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class SkillSet(BaseModel):
    """Compétences du candidat"""
    technical: List[str] = Field(default_factory=list, description="Compétences techniques")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills")
    languages: List[str] = Field(default_factory=list, description="Langues parlées")


class Period(BaseModel):
    """Période d'une expérience ou formation"""
    start: Optional[str] = Field(default=None, description="Date de début")
    end: Optional[str] = Field(default=None, description="Date de fin")


class Experience(BaseModel):
    """Expérience professionnelle"""
    title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Nom de l'entreprise")
    period: Period = Field(default_factory=Period, description="Période d'emploi")
    missions: List[str] = Field(default_factory=list, description="Missions principales")


class Education(BaseModel):
    """Formation"""
    degree: str = Field(..., description="Diplôme obtenu")
    school: str = Field(..., description="École/Université")
    period: Period = Field(default_factory=Period, description="Période de formation")


class CVData(BaseModel):
    """Données extraites d'un CV"""
    title: str = Field(..., description="Titre du CV / Poste recherché")
    address_city: str = Field(..., description="Ville du candidat")
    address_country: str = Field(default="France", description="Pays du candidat")
    summary: Optional[str] = Field(default=None, description="Résumé du profil")
    skills: SkillSet = Field(default_factory=SkillSet, description="Compétences")
    experience: List[Experience] = Field(default_factory=list, description="Expériences professionnelles")
    education: List[Education] = Field(default_factory=list, description="Formations")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    keywords: List[str] = Field(default_factory=list, description="Mots-clés")
    
    @classmethod
    def from_dict(cls, data: dict) -> "CVData":
        """Crée un CVData à partir d'un dictionnaire (avec normalisation)"""
        # Normaliser les données (gérer les différents formats)
        normalized = data.copy()
        
        # Format image (prompt_image.txt)
        if "ville_candidat" in normalized:
            normalized["address_city"] = normalized.pop("ville_candidat")
        if "type_poste" in normalized:
            normalized["title"] = normalized.pop("type_poste")
        if "description_candidat" in normalized and not normalized.get("summary"):
            normalized["summary"] = normalized.pop("description_candidat")
        if "competences" in normalized and not normalized.get("skills"):
            competences = normalized.pop("competences", [])
            normalized["skills"] = {
                "technical": competences if isinstance(competences, list) else [],
                "soft_skills": [],
                "languages": []
            }
        
        # S'assurer que les champs essentiels existent
        if not normalized.get("title"):
            normalized["title"] = "Developer"
        if not normalized.get("address_country"):
            normalized["address_country"] = "France"
        if not normalized.get("skills"):
            normalized["skills"] = {
                "technical": [],
                "soft_skills": [],
                "languages": []
            }
        if not normalized.get("keywords"):
            normalized["keywords"] = []
        
        # Convertir les expériences en objets Experience
        if normalized.get("experience"):
            normalized["experience"] = [
                Experience(**exp) if isinstance(exp, dict) else exp
                for exp in normalized["experience"]
            ]
        
        # Convertir les formations en objets Education
        if normalized.get("education"):
            normalized["education"] = [
                Education(**edu) if isinstance(edu, dict) else edu
                for edu in normalized["education"]
            ]
        
        return cls(**normalized)

