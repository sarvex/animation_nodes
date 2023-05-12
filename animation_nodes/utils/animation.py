from . blender_ui import iterActiveScreens

def isAnimationPlaying():
    return any(screen.is_animation_playing for screen in iterActiveScreens())

def isAnimated(idObject):
    if not idObject:
        return False

    if animationData := idObject.animation_data:
        return (
            True
            if animationData.action and len(animationData.action.fcurves) != 0
            else len(animationData.drivers) != 0
            or len(animationData.nla_tracks) != 0
        )
    else:
        return False
