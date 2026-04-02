from Autodesk.Revit.DB import *
 from pyrevit import revit, forms

doc = revit.doc

# Collect Mechanical Equipment
 collector = FilteredElementCollector(doc)\
 .OfCategory(BuiltInCategory.OST_MechanicalEquipment)\
 .WhereElementIsNotElementType()\
 .ToElements()

# Filter elements with "SP" in Comments
 filtered_elems = []
 errors = []

for el in collector:
 comment_param = el.LookupParameter("Comments")
 if comment_param and comment_param.HasValue:
 comment_val = comment_param.AsString()
 if comment_val and "SP" in comment_val:
 # Extract last digit
 last_digit = None
                                      for char in reversed(comment_val):
                                      if char.isdigit():
                                      last_digit = int(char)
                                      break

 if last_digit is not None:
#in c sharp it is 
#List<(el,lastdihigt)> felem which states List<tuple(key,pair)>
#to find it is felme.Add((ek,lastfgit))
                                      filtered_elems.append((el, last_digit))
 else:
 errors.append("No digit in Comments for element ID {}".format(el.Id))
 else:
 errors.append("Missing Comments for element ID {}".format(el.Id))

if not filtered_elems:
 forms.alert("No Mechanical Equipment found with 'SP' in Comments.", exitscript=True)

# Sort based on last digit seting rule how to sort 
# lamda x as x(firstindex)
                                      filtered_elems.sort(key=lambda x: x[1])

# Start transaction
 t = Transaction(doc, "Update Mechanical Equipment Parameters")
 t.Start()
# i is index enumerate is = [0,el,digit] it adds index
                                 for i, (el, digit) in enumerate(filtered_elems):
                                  try:
 # Set common parameters
 params_to_set = {
 "SENSIBLE CAPCITY (KW)": "WASTE WATER",
 "Location_Txt": "BASEMENT 1",
 "Mark": "4.7",
 "Floor_Txt": "7.8"
 }
# .items()
                                   for pname, val in params_to_set.items():
 p = el.LookupParameter(pname)
 if p and not p.IsReadOnly:
                                    if p.StorageType == StorageType.String:
                                    p.Set(val)
 elif p.StorageType == StorageType.Integer:
 p.Set(int(val))
 else:
 p.Set(val)
 else:
 errors.append("Parameter '{}' not found or read-only for element ID {}".format(pname, el.Id))

 # Toilet logic
 toilet_param = el.LookupParameter("Toilet")
 if toilet_param and not toilet_param.IsReadOnly:
 if i == 0:
 toilet_param.Set("1 WORKING")
 else:
 toilet_param.Set("1 ASSIST")
 else:
 errors.append("Toilet parameter missing for element ID {}".format(el.Id))

 except Exception as e:
 errors.append("Error updating element ID {}: {}".format(el.Id, str(e)))

t.Commit()

# Show result
 if errors:
 forms.alert("Completed with issues:\n\n" + "\n".join(errors))
 else:
 forms.alert("All Mechanical Equipment updated successfully!")
